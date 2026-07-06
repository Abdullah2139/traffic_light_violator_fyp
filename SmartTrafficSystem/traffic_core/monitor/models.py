from django.db import models

class Violation(models.Model):
    plate_number = models.CharField(max_length=20, default="UNKNOWN")
    vehicle_type = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    fine_amount = models.IntegerField(default=500) # image_evidence will store the photo of the violation
    image_evidence = models.ImageField(upload_to='violations/', null=True, blank=True)

    def __str__(self):
        return f"{self.plate_number} ({self.vehicle_type}) - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"