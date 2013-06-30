# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'CommentLike'
        db.delete_table(u'storage_commentlike')

        # Removing M2M table for field user on 'CommentLike'
        db.delete_table('storage_commentlike_user')

        # Deleting model 'Comment'
        db.delete_table(u'storage_comment')


    def backwards(self, orm):
        # Adding model 'CommentLike'
        db.create_table(u'storage_commentlike', (
            ('comment', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['storage.Comment'], unique=True)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['CommentLike'])

        # Adding M2M table for field user on 'CommentLike'
        db.create_table(u'storage_commentlike_user', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('commentlike', models.ForeignKey(orm[u'storage.commentlike'], null=False)),
            ('user', models.ForeignKey(orm[u'auth.user'], null=False))
        ))
        db.create_unique(u'storage_commentlike_user', ['commentlike_id', 'user_id'])

        # Adding model 'Comment'
        db.create_table(u'storage_comment', (
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('entry', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.Entry'])),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'storage', ['Comment'])


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
        u'storage.entry': {
            'Meta': {'ordering': "['-id']", 'object_name': 'Entry'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'author_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'available_in_frame': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'entry_id': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '512'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['storage.Feed']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '512'}),
            'published_at': ('django.db.models.fields.DateTimeField', [], {}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['storage.EntryTag']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        },
        u'storage.entrylike': {
            'Meta': {'object_name': 'EntryLike'},
            'entry': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['storage.Entry']", 'unique': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'})
        },
        u'storage.entrytag': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EntryTag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'})
        },
        u'storage.feed': {
            'Meta': {'ordering': "('title', 'feed_url')", 'object_name': 'Feed'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'encoding': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'entries_last_month': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'etag': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'feed_url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'}),
            'hub': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'last_entry_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'min_to_decay': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'next_scheduled_update': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'subtitle': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'tagline': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
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