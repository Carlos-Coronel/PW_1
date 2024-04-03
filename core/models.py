from django.db import models

class PDF(models.Model):
    nombre = models.CharField(max_length=100)
    materia = models.CharField(max_length=100)
    carrera = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20)
    objetivos = models.TextField()#Para textos largos como fundamentos, bibliografia, etc

    def __str__(self):
        return self.archivo
