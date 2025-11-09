# File Upload Implementation for WebApp Admin

## Overview
This document describes the file upload functionality implementation for the WebApp admin panel.

## Components

### 1. Database Model (`models.py`)
Enhanced `WebAppFile` model with the following fields:
- `id`: Primary key
- `telegram_file_id`: Optional Telegram file ID (if uploaded via bot)
- `storage_path`: Relative path to the uploaded file
- `file_type`: Type of file (IMAGE, DOCUMENT, VIDEO)
- `mime_type`: MIME type of the uploaded file
- `file_size`: File size in bytes
- `original_name`: Original filename from upload
- `description`: Optional description text
- `tag`: Optional tag label
- `width`: Image width (for images only)
- `height`: Image height (for images only)
- `uploaded_by`: Foreign key to User
- `created_at`: Upload timestamp

### 2. Configuration (`config.py`)
Added new settings:
- `webapp_upload_dir`: Upload directory path (default: `webapp/uploads`)
- `webapp_max_upload_size`: Maximum upload size in bytes (default: 10MB)

### 3. Storage Module (`webapp/storage.py`)
Utility functions for file storage:
- `get_upload_directory()`: Returns absolute upload directory path, creates if needed
- `build_storage_path(filename)`: Returns DB-relative storage path
- `resolve_physical_path(storage_path)`: Maps DB path to physical filesystem path
- `get_upload_url_prefix()`: Returns URL prefix for uploaded files

### 4. Upload Route (`webapp/routes/admin.py`)

#### POST /webapp/upload (Admin-only)
Accepts multipart form data:
- `file`: File to upload (required)
- `description`: Optional description text
- `tag`: Optional tag label

**Supported file types:**
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`
- **Documents**: `.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`, `.ppt`, `.pptx`, `.txt`
- **Videos**: `.mp4`, `.mpeg`, `.mpg`, `.mov`, `.avi`, `.webm`, `.mkv`

**Validation:**
- Checks MIME type against allowed types
- Checks file extension
- Validates file size against `webapp_max_upload_size`
- Returns 400 for unsupported types or oversized files

**Process:**
1. Validates file type and size
2. Generates UUID-based filename with original extension
3. Saves file asynchronously to upload directory
4. For images: extracts dimensions (width/height) using Pillow
5. Creates database record with metadata
6. Returns JSON with file ID, URL, and metadata

**Response schema:**
```json
{
  "id": 1,
  "file_type": "IMAGE",
  "file_url": "http://localhost:8000/webapp/uploads/abc123.png",
  "mime_type": "image/png",
  "file_size": 12345,
  "original_name": "my_photo.png",
  "description": "Test image",
  "tag": "category1",
  "width": 800,
  "height": 600
}
```

#### DELETE /webapp/file/{file_id} (Admin-only)
Deletes both the database record and physical file from disk.

**Response:**
```json
{
  "success": true,
  "message": "Файл удалён"
}
```

### 5. Service Layer (`services/webapp_content_service.py`)
Enhanced methods:
- `create_file()`: Creates file record with all metadata fields
- `delete_file()`: Deletes file record and optionally physical file
- `get_file()`: Retrieves file record by ID

### 6. Static File Mounting (`webapp/server.py`)
The upload directory is mounted as static files:
```python
app.mount("/webapp/uploads", StaticFiles(directory=str(upload_dir)), name="webapp_uploads")
```

Files are accessible at: `{webapp_public_url}/webapp/uploads/{filename}`

### 7. URL Building (`webapp/routes/categories.py`)
Enhanced `build_file_url()` function to handle upload paths:
- Returns `telegram_file_id` if available
- For local files, builds URL using `webapp_public_url`
- Handles both `webapp/static/` and `webapp/uploads/` paths

## Security

1. **Admin-only access**: Upload endpoint requires `require_admin_user` dependency
2. **File type validation**: Only allowed MIME types and extensions accepted
3. **Size limits**: Configurable maximum file size
4. **UUID filenames**: Prevents path traversal and filename conflicts
5. **Directory isolation**: Uploads stored in dedicated directory outside static assets

## Testing

Comprehensive test suite in `tests/test_webapp_uploads.py`:
- Upload image as admin
- Upload PDF as admin
- Non-admin receives 403
- Invalid file type returns 400
- File deletion
- Physical file storage verification

## Usage Example

### Upload a file:
```bash
curl -X POST http://localhost:8000/webapp/upload \
  -H "X-Telegram-Init-Data: {signed_init_data}" \
  -F "file=@photo.jpg" \
  -F "description=Product photo" \
  -F "tag=products"
```

### Use uploaded file in category item:
```bash
curl -X POST http://localhost:8000/webapp/category/1/items \
  -H "X-Telegram-Init-Data: {signed_init_data}" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "IMAGE",
    "file_id": 1,
    "text_content": "Product description",
    "order_index": 0
  }'
```

### Delete a file:
```bash
curl -X DELETE http://localhost:8000/webapp/file/1 \
  -H "X-Telegram-Init-Data: {signed_init_data}"
```

## Dependencies

Added to `requirements.txt`:
- `pillow==10.2.0`: For image dimension extraction

## Configuration

Environment variables (optional):
```env
WEBAPP_UPLOAD_DIR=webapp/uploads
WEBAPP_MAX_UPLOAD_SIZE=10485760  # 10MB in bytes
```

## Notes

1. Uploaded files are excluded from git via `.gitignore`
2. Files are served as static content - no authentication required for access
3. Physical files are deleted when the database record is deleted
4. Image dimensions are automatically extracted and stored
5. All logging is in Russian with success/error icons
