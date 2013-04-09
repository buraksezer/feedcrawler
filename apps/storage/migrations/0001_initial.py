# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Feed'
        db.create_table(u'storage_feed', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed_url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_sync', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('updated_at', self.gf('django.db.models.fields.DateField')(null=True)),
        ))
        db.send_create_signal(u'storage', ['Feed'])

        # Adding M2M table for field users on 'Feed'
        db.create_table(u'storage_feed_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feed', models.ForeignKey(orm[u'storage.feed'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'storage_feed_users', ['feed_id', 'user_id'])

        # Adding model 'FeedMetadata'
        db.create_table(u'storage_feedmetadata', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('link', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('encoding', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('subtitle', self.gf('django.db.models.fields.CharField')(max_length=512, null=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Feed'])),
        ))
        db.send_create_signal(u'storage', ['FeedMetadata'])

        # Adding model 'FeedTag'
        db.create_table(u'storage_feedtag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
        ))
        db.send_create_signal(u'storage', ['FeedTag'])

        # Adding M2M table for field feed on 'FeedTag'
        db.create_table(u'storage_feedtag_feed', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feedtag', models.ForeignKey(orm[u'storage.feedtag'], null=False)),
            ('feed', models.ForeignKey(orm[u'storage.feed'], null=False))
        ))
        db.create_unique(u'storage_feedtag_feed', ['feedtag_id', 'feed_id'])

        # Adding M2M table for field users on 'FeedTag'
        db.create_table(u'storage_feedtag_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('feedtag', models.ForeignKey(orm[u'storage.feedtag'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'storage_feedtag_users', ['feedtag_id', 'user_id'])

        # Adding model 'Entry'
        db.create_table(u'storage_entry', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=512)),
            ('published_at', self.gf('django.db.models.fields.DateField')(null=True)),
            ('updated_at', self.gf('django.db.models.fields.DateField')(null=True)),
            ('entry_id', self.gf('django.db.models.fields.URLField')(unique=True, max_length=512)),
            ('license', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, blank=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Feed'])),
        ))
        db.send_create_signal(u'storage', ['Entry'])

        # Adding model 'EntryTag'
        db.create_table(u'storage_entrytag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tag', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
        ))
        db.send_create_signal(u'storage', ['EntryTag'])

        # Adding M2M table for field entry on 'EntryTag'
        db.create_table(u'storage_entrytag_entry', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entrytag', models.ForeignKey(orm[u'storage.entrytag'], null=False)),
            ('entry', models.ForeignKey(orm[u'storage.entry'], null=False))
        ))
        db.create_unique(u'storage_entrytag_entry', ['entrytag_id', 'entry_id'])

        # Adding model 'Comment'
        db.create_table(u'storage_comment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('entry', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.Entry'], unique=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal(u'storage', ['Comment'])


    def backwards(self, orm):
        # Deleting model 'Feed'
        db.delete_table(u'storage_feed')

        # Removing M2M table for field users on 'Feed'
        db.delete_table('storage_feed_users')

        # Deleting model 'FeedMetadata'
        db.delete_table(u'storage_feedmetadata')

        # Deleting model 'FeedTag'
        db.delete_table(u'storage_feedtag')

        # Removing M2M table for field feed on 'FeedTag'
        db.delete_table('storage_feedtag_feed')

        # Removing M2M table for field users on 'FeedTag'
        db.delete_table('storage_feedtag_users')

        # Deleting model 'Entry'
        db.delete_table(u'storage_entry')

        # Deleting model 'EntryTag'
        db.delete_table(u'storage_entrytag')

        # Removing M2M table for field entry on 'EntryTag'
        db.delete_table('storage_entrytag_entry')

        # Deleting model 'Comment'
        db.delete_table(u'storage_comment')


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
            'content': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'entry_id': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '512'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '512'}),
            'published_at': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
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
            'feed_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateField', [], {'null': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'storage.feedmetadata': {
            'Meta': {'object_name': 'FeedMetadata'},
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'})
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