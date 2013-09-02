# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'Interaction'
        db.delete_table(u'storage_interaction')

        # Deleting model 'Entry'
        db.delete_table(u'storage_entry')

        # Removing M2M table for field tags on 'Entry'
        db.delete_table('storage_entry_tags')

        # Deleting model 'ReadLater'
        db.delete_table(u'storage_readlater')

        # Deleting model 'RepostEntry'
        db.delete_table(u'storage_repostentry')

        # Deleting model 'Comment'
        db.delete_table(u'storage_comment')

        # Deleting model 'EntryLike'
        db.delete_table(u'storage_entrylike')


    def backwards(self, orm):
        # Adding model 'Interaction'
        db.create_table(u'storage_interaction', (
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Entry'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'storage', ['Interaction'])

        # Adding model 'Entry'
        db.create_table(u'storage_entry', (
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Feed'])),
            ('license', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('language', self.gf('django.db.models.fields.CharField')(max_length=128, null=True)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('author_email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('available_in_frame', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_modified', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(populate_from='title', unique=True, max_length=50, null=True, unique_with=())),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('last_interaction', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('published_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('entry_id', self.gf('django.db.models.fields.URLField')(max_length=2048, unique=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=2048)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['Entry'])

        # Adding M2M table for field tags on 'Entry'
        db.create_table(u'storage_entry_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entry', models.ForeignKey(orm[u'storage.entry'], null=False)),
            ('entrytag', models.ForeignKey(orm[u'storage.entrytag'], null=False))
        ))
        db.create_unique(u'storage_entry_tags', ['entry_id', 'entrytag_id'])

        # Adding model 'ReadLater'
        db.create_table(u'storage_readlater', (
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Entry'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'storage', ['ReadLater'])

        # Adding model 'RepostEntry'
        db.create_table(u'storage_repostentry', (
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('note', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('target_ids', self.gf('django.db.models.fields.CommaSeparatedIntegerField')(max_length=200, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Entry'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['RepostEntry'])

        # Adding model 'Comment'
        db.create_table(u'storage_comment', (
            ('content', self.gf('django.db.models.fields.TextField')()),
            (u'interaction_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.Interaction'], unique=True, primary_key=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'storage', ['Comment'])

        # Adding model 'EntryLike'
        db.create_table(u'storage_entrylike', (
            (u'interaction_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.Interaction'], unique=True, primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['EntryLike'])


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
        u'storage.entrytag': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EntryTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
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
        u'storage.feedtag': {
            'Meta': {'object_name': 'FeedTag'},
            'feed': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['storage.Feed']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'storage.list': {
            'Meta': {'object_name': 'List'},
            'feed': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['storage.Feed']", 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'max_length': '50', 'unique': 'True', 'null': 'True', 'populate_from': "'title'", 'unique_with': '()'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['storage']