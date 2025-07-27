const fs = require('fs');
const path = require('path');
const glob = require('glob');

const PROJECT_ROOT = path.join(__dirname, '..', '..');

/**
 * Get all files (PDF, JPEG, PNG) for a project and return file information
 */
function getProjectFiles(fileLocation) {
    const absPath = path.resolve(fileLocation);
    const fileTypes = [
        { ext: 'pdf', type: 'pdf' },
        { ext: 'jpeg', type: 'img' },
        { ext: 'jpg', type: 'img' },
        { ext: 'png', type: 'img' }
    ];
    
    const allFiles = [];
    let mostRecent = null;

    for (const { ext, type } of fileTypes) {
        const pattern = path.join(absPath, `*.${ext}`);
        try {
            const files = glob.sync(pattern);
            
            for (const file of files) {
                const stats = fs.statSync(file);
                const ctime = stats.ctimeMs;
                
                const fileInfo = {
                    path: file,
                    type: type,
                    ctime: ctime,
                    filename: path.basename(file),
                    rel_path: path.relative(PROJECT_ROOT, file)
                };
                
                allFiles.push(fileInfo);

                if (!mostRecent || ctime > mostRecent.ctime) {
                    mostRecent = fileInfo;
                }
            }
        } catch (error) {
            // Continue if directory doesn't exist or other errors
            console.warn(`Warning: Could not scan directory ${absPath} for ${ext} files:`, error.message);
        }
    }

    // Sort files by creation time (newest first)
    allFiles.sort((a, b) => b.ctime - a.ctime);
    
    return {
        all_files: allFiles,
        file_count: allFiles.length,
        most_recent: mostRecent
    };
}

module.exports = {
    getProjectFiles,
    PROJECT_ROOT
};
