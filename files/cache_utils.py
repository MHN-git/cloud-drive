from django.core.cache import cache

def get_folder_files_cache_key(owner_id, folder_id):
    return f"user:{owner_id}:folder:{folder_id}:files"

def invalidate_folder_files_cache(owner_id, folder_id):
    cache.delete(get_folder_files_cache_key(owner_id, folder_id))