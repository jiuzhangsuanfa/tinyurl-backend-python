from django.db import models


class Visit(models.Model):
    long_url = models.CharField(max_length=1000)
    visit_num = models.IntegerField(default=0)
    create_date = models.DateTimeField("date create")

    def __str__(self):
        content = """
                long_url: {} 
            """.format(self.long_url)

        return content



