from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.contrib import admin
from django.core.urlresolvers import reverse
from taggit.managers import TaggableManager
import time

class Skill(models.Model):
    #user_profiles = models.ManyToManyField(UserProfile, null=True, blank=True)
    title = models.CharField( max_length=30 )

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('skill_detail', kwargs={'object_id': self.id})

    @classmethod
    def search(cls, q):
        return cls.objects.all().distinct().filter(
            Q(title__icontains=q)
            )

class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True)
    bio = models.TextField(blank=True)
    interests = TaggableManager( verbose_name='Interests', blank=True )
    location = models.CharField( max_length=100, blank=True )
    phone = models.CharField( max_length=20, blank=True, null=True )

    #city = models.CharField( max_length=50, blank=True )
    #state = models.CharField( max_length=50, blank=True )
    #postal_code = models.CharField( max_length=25, blank=True )
    url = models.URLField(blank=True)
    #skills = models.ManyToManyField(Skill, related_name='user_profiles', null=True, blank=True)
    avatar = models.ImageField(upload_to='/avatars/', blank=True, null=True)
    bg_image = models.ImageField(upload_to='/bg_images/', blank=True, null=True, verbose_name="Background image")

    def __unicode__(self):
        return self.user.__unicode__()

    def get_absolute_url(self):
        return reverse('general.views.view_profile', kwargs={'username':self.user.username})

def create_user_profile(sender, **kwargs):
    """ Creates a UserProfile for each new User """
    if kwargs['created'] == True:
        up = UserProfile(user=kwargs['instance'])
        up.save()
        
post_save.connect(create_user_profile, sender=User)


class Organization(models.Model):
    name = models.CharField(max_length = 255, unique=True)
    description = models.TextField(blank = True)
    url = models.URLField(blank = True)
    addr1 = models.CharField(verbose_name = "Address", max_length = 255, blank = True)
    addr2 = models.CharField(verbose_name = "Address (cont.)", max_length = 255, blank = True)
    city = models.CharField(max_length = 255, blank = True)
    state = models.CharField(max_length = 255, blank = True)
    postal_code = models.CharField(max_length = 255, blank = True)
    members = models.ManyToManyField(User, related_name="organizations")
    admin = models.ForeignKey(User)
    resources = models.ManyToManyField('Resource', related_name='owners', blank=True, null=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('organization_detail', kwargs={'object_id': self.id})

    @classmethod
    def search(cls, q):
        return cls.objects.all().distinct().filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(city__icontains=q) |
            Q(state__icontains=q) |
            Q(postal_code__icontains=q)
            )

class WorkingGroup(models.Model) :
    name = models.CharField(max_length=64, unique=True)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    members = models.ManyToManyField(User, related_name="working_groups")

    def __unicode__(self):
        return self.name

class Project(models.Model) :
    name = models.CharField(max_length=64)
    workinggroup = models.ForeignKey(WorkingGroup, on_delete=models.PROTECT)

    class Meta :
        unique_together = (("name", "workinggroup"))

    def __unicode__(self):
        return '%s\'s %s' % (self.workinggroup, self.name)

class TaskBase(models.Model) :
    STATE_NEW = 0
    STATE_WONT = 1
    STATE_DONE = 2
    STATE_REOPENED = 3

    description = models.TextField(blank=True, null=True)
    state = models.IntegerField(default=STATE_NEW, blank=True, null=True, choices=[
      (STATE_NEW, 'New'),
      (STATE_WONT, 'Won\'t Fix'),
      (STATE_DONE, 'Done'),
      (STATE_REOPENED, 'Reopened'),
    ])

    creator = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    assignee = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    ts = models.BigIntegerField()

    class Meta :
        abstract = True

class Task(TaskBase) :
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)

    def __unicode__(self):
        return 'Task %s in %s' % (self.name, self.project.name)

class TaskLog(TaskBase) :
    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    comment = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return '%s task log on %s' % (self.creator, self.task)

def log_change(sender, **kwargs):
    """ Updates the Task with the info from the TaskLog """
    if kwargs['created'] == False:
        raise RuntimeError("one does not simply modify the task log.")

    tasklog = kwargs['instance']
    task = tasklog.task
    if tasklog.description is not None :
       task.description = tasklog.description
    if tasklog.state is not None :
       task.state = tasklog.state
    if tasklog.assignee is not None :
       task.assignee = tasklog.assignee

    task.ts = long(time.time())
    task.save()
        
post_save.connect(log_change, sender=TaskLog)

class Resource(models.Model):
    name = models.CharField(max_length = 255)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('resource_detail', kwargs={'object_id': self.id})

    @classmethod
    def search(cls, q):
        return cls.objects.all().distinct().filter(
            Q(name__icontains=q)
            )


admin.site.register(Resource)
admin.site.register(Organization)
admin.site.register(Skill)
admin.site.register(UserProfile)
admin.site.register(WorkingGroup)
admin.site.register(Project)
admin.site.register(Task)
admin.site.register(TaskLog)
