# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Interaction'
        db.create_table(u'storage_interaction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.BaseEntry'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'storage', ['Interaction'])

        # Adding model 'Entry'
        db.create_table(u'storage_entry', (
            (u'baseentry_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.BaseEntry'], unique=True, primary_key=True)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(max_length=50, unique=True, null=True, populate_from='title', unique_with=())),
            ('entry_id', self.gf('django.db.models.fields.URLField')(unique=True, max_length=2048)),
        ))
        db.send_create_signal(u'storage', ['Entry'])

        # Adding model 'ReadLater'
        db.create_table(u'storage_readlater', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.BaseEntry'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'storage', ['ReadLater'])

        # Adding model 'RepostEntry'
        db.create_table(u'storage_repostentry', (
            (u'baseentry_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.BaseEntry'], unique=True, primary_key=True)),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(max_length=50, unique=True, null=True, populate_from='title', unique_with=())),
            ('entry_id', self.gf('django.db.models.fields.URLField')(unique=True, max_length=2048)),
        ))
        db.send_create_signal(u'storage', ['RepostEntry'])

        # Adding model 'BaseEntry'
        db.create_table(u'storage_baseentry', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('content', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('author_email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=2048, blank=True)),
            ('published_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('license', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
            ('available_in_frame', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('last_interaction', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Feed'])),
        ))
        db.send_create_signal(u'storage', ['BaseEntry'])

        # Adding model 'EntryLike'
        db.create_table(u'storage_entrylike', (
            (u'interaction_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.Interaction'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['EntryLike'])

        # Adding model 'Comment'
        db.create_table(u'storage_comment', (
            (u'interaction_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.Interaction'], unique=True, primary_key=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'storage', ['Comment'])


    def backwards(self, orm):
        # Adding model 'EntryTag'
        db.create_table(u'storage_entrytag', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, unique=True)),
        ))
        db.send_create_signal(u'storage', ['EntryTag'])

        # Adding model 'FeedTag'
        db.create_table(u'storage_feedtag', (
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=512, unique=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
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

        # Deleting model 'Interaction'
        db.delete_table(u'storage_interaction')

        # Deleting model 'Entry'
        db.delete_table(u'storage_entry')

        # Deleting model 'ReadLater'
        db.delete_table(u'storage_readlater')

        # Deleting model 'RepostEntry'
        db.delete_table(u'storage_repostentry')

        # Deleting model 'BaseEntry'
        db.delete_table(u'storage_baseentry')

        # Deleting model 'EntryLike'
        db.delete_table(u'storage_entrylike')

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
        u'storage.baseentry': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'BaseEntry'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'author_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'available_in_frame': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'last_interaction': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '2048', 'blank': 'True'}),
            'published_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        },
        u'storage.comment': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Comment', '_ormbases': [u'storage.Interaction']},
            'content': ('django.db.models.fields.TextField', [], {}),
            u'interaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['storage.Interaction']", 'unique': 'True', 'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'storage.entry': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'Entry', '_ormbases': [u'storage.BaseEntry']},
            u'baseentry_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['storage.BaseEntry']", 'unique': 'True', 'primary_key': 'True'}),
            'entry_id': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '2048'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'populate_from': "'title'", 'unique_with': '()'})
        },
        u'storage.entrylike': {
            'Meta': {'ordering': "['-id']", 'object_name': 'EntryLike', '_ormbases': [u'storage.Interaction']},
            u'interaction_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['storage.Interaction']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'storage.feed': {
            'Meta': {'ordering': "('title', 'feed_url')", 'object_name': 'Feed'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            'entries_last_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'etag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'feed_url': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'hub': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'last_entry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            'min_to_decay': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'next_scheduled_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'populate_from': "'title'", 'unique_with': '()'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            'tagline': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateField', [], {'null': 'True'})
        },
        u'storage.interaction': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Interaction'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.BaseEntry']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'storage.list': {
            'Meta': {'object_name': 'List'},
            'feed': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['storage.Feed']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'populate_from': "'title'", 'unique_with': '()'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'storage.readlater': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'ReadLater'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'entry': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.BaseEntry']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'storage.repostentry': {
            'Meta': {'ordering': "['-created_at']", 'object_name': 'RepostEntry', '_ormbases': [u'storage.BaseEntry']},
            u'baseentry_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['storage.BaseEntry']", 'unique': 'True', 'primary_key': 'True'}),
            'entry_id': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '2048'}),
            'note': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'populate_from': "'title'", 'unique_with': '()'})
        }
    }

    complete_apps = ['storage']
