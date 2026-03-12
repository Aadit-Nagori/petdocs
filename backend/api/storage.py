import os

from storages.backends.s3 import S3Storage


class SupabasePublicStorage(S3Storage):
    def url(self, name):
        project_url = os.getenv('SUPABASE_PROJECT_URL')
        bucket = os.getenv('SUPABASE_BUCKET_NAME')
        return f"{project_url}/storage/v1/object/public/{bucket}/{name}"
