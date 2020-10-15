from django.db import models

from tinyurl.settings import DOMAIN


class Long2Short(models.Model):
    long_url = models.CharField(max_length=1000)
    short_key = models.CharField(max_length=10, db_index=True, unique=True)
    created_at = models.DateTimeField("created_at", auto_now_add=True)
    ip_address = models.CharField(max_length=100, null=True)

    def __str__(self):
        content = """
            long_url: {} ==> short_url: {}{}/
        """.format(self.long_url, DOMAIN, self.short_key)

        return content


class Long2ShortV2(models.Model):
    long_url = models.CharField(max_length=1000)
    created_at = models.DateTimeField("created_at")
    ip_address = models.CharField(max_length=100, null=True)

    def __str__(self):
        content = """
                long_url: {} 
            """.format(self.long_url)

        return content

