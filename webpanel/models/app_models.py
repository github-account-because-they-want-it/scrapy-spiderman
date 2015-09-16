from __future__ import unicode_literals
from os import path as pth
import uuid
import warnings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.utils import timesince, timezone
from django.conf import settings
from scrapy import Field


class SpiderProject(models.Model):

    path = models.CharField(max_length=255, null=False, blank=False,
                            verbose_name=_("Path to a spider project found in SPIDER_DIRS setting"))

    class Meta:
        app_label = "webpanel"
        ordering = ("path",)


class Spider(models.Model):

    name = models.CharField(max_length=255, null=False, blank=False)
    item_model_name = models.CharField(max_length=128, blank=False, null=False,
                                       help_text=_("Used to refer to the item model for this spider"))
    project = models.ForeignKey(SpiderProject, related_name="spiders")

    class Meta:
        app_label = "webpanel"
        ordering = ("name",)

    @property
    def item_model(self):
        return ContentType.objects.get_by_natural_key("webpanel", self.item_model_name).model_class()

    def run(self):
        pass

    def stop(self):
        pass

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<Spider {}>".format(self.name)


def logfile_uploadto(spider_run, filename):
    return pth.join(settings.MEDIA_ROOT, "spider_logs", spider_run.spider.name, str(uuid.uuid4()) + ".log")


class SpiderRun(models.Model):

    FINISH_REASON_FAILED = "FL"
    FINISH_REASON_FINISHED = "FN"
    FINISH_REASON_USER = "FUSR"

    FINISH_CHOICES = (
        (FINISH_REASON_FAILED, "Failed"),
        (FINISH_REASON_FINISHED, "Finished"),
        (FINISH_REASON_USER, "Stopped by user")
    )

    spider = models.ForeignKey(Spider, related_name="runs")
    start_time = models.DateTimeField(auto_now_add=True, editable=False)
    finish_time = models.DateTimeField(null=True, blank=True, editable=False)
    finish_reason = models.CharField(choices=FINISH_CHOICES, max_length=32, editable=False)
    stopped = models.BooleanField(default=False, editable=False,
                                  help_text=_("Whether the user asked to stop the related spider"))
    logfile = models.FileField(upload_to=logfile_uploadto)

    class Meta:
        ordering = ("start_time",)
        app_label = "webpanel"

    @property
    def finished(self):
        return self.finish_time is not None

    @property
    def runtime(self):
        return timesince(self.start_time, timezone.now() if self.finish_time is None else self.finish_time)

    def save(self, *args, **kwargs):
        assert self.finish_time is None or \
               self.finish_time > self.start_time, "You've got a nice time machine, still this won't pass"
        return super(SpiderRun, self).save(*args, **kwargs)

    def save_item(self, item):
        ITEM_MODEL = ContentType.objects.get_by_natural_key("webpanel", self.spider.item_model_name)
        itemmodel_fieldnames = [field.name for field in ITEM_MODEL._meta.fields]
        model_instance = ITEM_MODEL()
        for fieldname, field in item.fields:
            if isinstance(field, Field) and fieldname in itemmodel_fieldnames:
                if fieldname == "spider":
                    warnings.warn("Use of 'spider' item attribute is reserved. Skipping field.", UserWarning)
                    continue
                setattr(model_instance, fieldname, item[fieldname])
        self.save()

    @property
    def items(self):
        # retrieves the items related manager for this run
        return getattr(self, "%s_%s_items" % ("webpanel", self.spider.item_model_name))

    def __unicode__(self):
        datetime_fmt = "%d-%m-%Y %H:%M:%S %p"
        return "{} running from [{}] {}".format(self.spider.name, self.start_time.strftime(datetime_fmt),
                                                ", finished at {}".format(self.finish_time.strftime(datetime_fmt))
                                                if self.finished else "[Still running...]")


class BaseItem(models.Model):

    # %(class)s stands for subclass name
    spider_run = models.ForeignKey(SpiderRun, related_name="%(app_label)s_%(class)s_items")

    class Meta:
        app_label = "webpanel"
        abstract = True

    def __unicode__(self):
        return "Item for spider '{}'".format(self.spider_run.spider.name)

    def __repr__(self):
        return "<BaseItem, spider={}>".format(self.spider_run.spider.name)
