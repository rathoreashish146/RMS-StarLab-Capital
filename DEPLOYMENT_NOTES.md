# RMS Deployment Notes

## ⚠️ Important: Ephemeral Storage on Render

### The Issue
Render (and many cloud platforms) use **ephemeral storage**, meaning:
- Files uploaded to the local filesystem are **deleted** on each deployment
- Any restart, redeployment, or scaling event will **wipe all uploaded files**
- The `uploads/` folder is **not persistent**

### Current Impact
- Bills and invoices uploaded by users will be lost on the next deployment
- Users will see "File Not Found" errors when trying to download old bills
- This is a **platform limitation**, not a bug in the application

### Solutions

#### Option 1: Use Cloud Storage (Recommended) ✅
Integrate a persistent storage service like:
- **AWS S3** - Most popular, pay-as-you-go
- **Google Cloud Storage** - Good alternative
- **Cloudinary** - Good for images/documents
- **Azure Blob Storage** - If using Microsoft ecosystem

**Benefits:**
- Files persist forever
- Scalable and reliable
- Better performance
- Can serve files directly from CDN

**Implementation:** Would require modifying the upload/download code to use cloud storage SDK

#### Option 2: Store Files in Database
Store files as binary data (BLOB) in PostgreSQL

**Benefits:**
- No additional service needed
- Files backed up with database

**Drawbacks:**
- Larger database size
- Slower performance for large files
- More expensive database hosting

#### Option 3: Use Render Persistent Disks
Render offers persistent disk storage (paid feature)

**Benefits:**
- Simple to implement
- Files persist across deployments

**Drawbacks:**
- Additional cost ($2-10/month depending on size)
- Single instance only (no horizontal scaling)
- Requires upgrading to paid plan

### Current Workaround
Users need to **re-upload bills** after each deployment. The application will:
- Show a friendly error message when files are missing
- Allow easy re-upload of documents
- Warn users about the ephemeral storage limitation

### Recommended Next Steps
1. **Immediate:** Add warning message in UI about file persistence
2. **Short-term:** Implement AWS S3 or similar cloud storage
3. **Long-term:** Consider Render persistent disks for simpler setup

## Database Connection Settings

The application now includes:
- **Connection pooling** (10 connections, max 30)
- **Pre-ping** to test connections before use
- **Automatic retry** (3 attempts) for failed queries
- **Connection recycling** every hour
- **Timeout protection** (30 seconds per query)

These settings handle intermittent SSL/connection errors that can occur with PostgreSQL on Render.

## Environment Variables

Required:
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Render)
- `RMS_SECRET` - Flask session secret key

Optional:
- `RMS_UPLOAD_DIR` - Custom upload directory (defaults to `./uploads`)

## Monitoring

Check logs for:
- `❌ File not found:` - Files that were uploaded before last deployment
- `⚠️ Database connection error` - Retrying connection
- `✅ Saved file:` - Successful file uploads (will be lost on next deployment)

## Support

For questions about:
- **Storage options:** Contact your cloud storage provider
- **Render persistent disks:** See https://render.com/docs/disks
- **Application issues:** Check the application logs

