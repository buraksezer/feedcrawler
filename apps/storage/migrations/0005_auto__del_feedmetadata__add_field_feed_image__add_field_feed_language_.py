# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'FeedMetadata'
        db.delete_table(u'storage_feedmetadata')

        # Adding field 'Feed.image'
        db.add_column(u'storage_feed', 'image',
                      self.gf('django.db.models.fields.CharField')(max_length=1024, null=True),
                      keep_default=False)

        # Adding field 'Feed.language'
        db.add_column(u'storage_feed', 'language',
                      self.gf('django.db.models.fields.CharField')(max_length=128, null=True),
                      keep_default=False)

        # Adding field 'Feed.title'
        db.add_column(u'storage_feed', 'title',
                      self.gf('django.db.models.fields.CharField')(max_length=512, null=True),
                      keep_default=False)

        # Adding field 'Feed.link'
        db.add_column(u'storage_feed', 'link',
                      self.gf('django.db.models.fields.CharField')(max_length=512, null=True),
                      keep_default=False)

        # Adding field 'Feed.encoding'
        db.add_column(u'storage_feed', 'encoding',
                      self.gf('django.db.models.fields.CharField')(max_length=128, null=True),
                      keep_default=False)

        # Adding field 'Feed.subtitle'
        db.add_column(u'storage_feed', 'subtitle',
                      self.gf('django.db.models.fields.CharField')(max_length=512, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding model 'FeedMetadata'
        db.create_table(u'storage_feedmetadata', (
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Feed'])),
            ('link', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('encoding', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('subtitle', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('image', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['FeedMetadata'])

        # Deleting field 'Feed.image'
        db.delete_column(u'storage_feed', 'image')

        # Deleting field 'Feed.language'
        db.delete_column(u'storage_feed', 'language')

        # Deleting field 'Feed.title'
        db.delete_column(u'storage_feed', 'title')

        # Deleting field 'Feed.link'
        db.delete_column(u'storage_feed', 'link')

        # Deleting field 'Feed.encoding'
        db.delete_column(u'storage_feed', 'encoding')

        # Deleting field 'Feed.subtitle'
        db.delete_column(u'storage_feed', 'subtitle')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'storage.comment': {
            'Meta': {'object_name': 'Comment'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'entry': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['storage.Entry']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'storage.entry': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Entry'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'entry_id': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '512'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '512'}),
            'published_at': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'updated_at': ('django.db.models.fields.DateField', [], {'null': 'True'})
        },
        u'storage.entrytag': {
            'Meta': {'object_name': 'EntryTag'},
            'entry': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['storage.Entry']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'})
        },
        u'storage.feed': {
            'Meta': {'object_name': 'Feed'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'feed_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'storage.feedtag': {
            'Meta': {'object_name': 'FeedTag'},
            'feed': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['storage.Feed']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['storage']