from mongoengine import FloatField
from mongoengine.document import Document
from mongoengine.fields import StringField


class FlowsInformations(Document):

    source_ip = StringField(required=True)
    destination_ip = StringField(required=True)
    destination_ip_2 = StringField(required=True)
    date = StringField(required=True)
    hour = StringField(required=True)
    traffic_type = StringField(required=True)
    bandwidth = FloatField()
    first_timestamp = FloatField()
    last_timestamp = FloatField()

    meta = {
        'index_background': True,
        'indexes': [
            'source_ip',
            'destination_ip', 'date', 'bandwidth'
        ]
    }

    def __str__(self):
        return 'save result from %s at %s with %s' % (self.source_ip, self.date, self.traffic_type)
