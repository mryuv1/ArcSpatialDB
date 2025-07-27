class ArcSpatialDBClient {
    constructor(baseUrl = 'http://localhost:5000') {
        this.baseUrl = baseUrl;
        this.userNames = [];
        this.currentFiles = [];
        this.currentFileIndex = 0;
        this.init();
    }

    async init() {
        await this.loadUserNames();
        this.initEventListeners();
        this.loadAllProjects();
        this.loadAllAreas();
    }

    // API Methods
    async apiRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    async loadUserNames() {
        try {
            const data = await this.apiRequest('/api/user_names');
            this.userNames = data.user_names;
            this.populateUserNameDropdown();
        } catch (error) {
            this.showError('Failed to load user names: ' + error.message);
        }
    }

    async searchProjects(searchData) {
        try {
            this.showLoading('search-results', true);
            const data = await this.apiRequest('/api/projects/search', {
                method: 'POST',
                body: JSON.stringify(searchData)
            });
            this.displaySearchResults(data.results);
        } catch (error) {
            this.showError('Search failed: ' + error.message);
            this.displaySearchResults([]);
        } finally {
            this.showLoading('search-results', false);
        }
    }

    async loadAllProjects(page = 1, filters = {}) {
        try {
            this.showLoading('all-projects', true);
            const params = new URLSearchParams({
                page: page.toString(),
                per_page: '10',
                ...filters
            });
            
            const data = await this.apiRequest(`/api/projects?${params}`);
            this.displayAllProjects(data);
        } catch (error) {
            this.showError('Failed to load projects: ' + error.message);
        } finally {
            this.showLoading('all-projects', false);
        }
    }

    async loadAllAreas(page = 1, filters = {}) {
        try {
            this.showLoading('all-areas', true);
            const params = new URLSearchParams({
                page: page.toString(),
                per_page: '10',
                ...filters
            });
            
            const data = await this.apiRequest(`/api/areas?${params}`);
            this.displayAllAreas(data);
        } catch (error) {
            this.showError('Failed to load areas: ' + error.message);
        } finally {
            this.showLoading('all-areas', false);
        }
    }

    async deleteProject(uuid) {
        if (!confirm('Are you sure you want to delete this project?')) {
            return;
        }

        try {
            await this.apiRequest(`/api/projects/${uuid}`, { method: 'DELETE' });
            this.showSuccess('Project deleted successfully');
            this.loadAllProjects(); // Reload projects table
        } catch (error) {
            this.showError('Failed to delete project: ' + error.message);
        }
    }

    async getProjectFiles(uuid) {
        try {
            const data = await this.apiRequest(`/api/projects/${uuid}/files`);
            return data;
        } catch (error) {
            this.showError('Failed to load project files: ' + error.message);
            return { all_files: [], file_count: 0, most_recent: null };
        }
    }

    // UI Methods
    initEventListeners() {
        // Search form
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSearch();
            });
        }

        // Reset button
        const resetBtn = document.getElementById('resetBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetForm();
            });
        }

        // Add user name button
        const addUserNameBtn = document.getElementById('addUserNameBtn');
        if (addUserNameBtn) {
            addUserNameBtn.addEventListener('click', () => {
                this.addUserNameDropdown();
            });
        }

        // Paper size select
        const paperSizeSelect = document.getElementById('paper_size_select');
        if (paperSizeSelect) {
            paperSizeSelect.addEventListener('change', () => {
                this.toggleCustomSize();
            });
        }

        // Relative size checkbox
        const relativeSizeCheckbox = document.getElementById('relative_size_checkbox');
        if (relativeSizeCheckbox) {
            relativeSizeCheckbox.addEventListener('change', () => {
                this.toggleRelativeSize();
            });
        }

        // Keyboard navigation for gallery
        document.addEventListener('keydown', (event) => {
            if (document.getElementById('galleryModal').style.display === 'flex') {
                if (event.key === 'ArrowLeft') {
                    this.previousFile();
                } else if (event.key === 'ArrowRight') {
                    this.nextFile();
                } else if (event.key === 'Escape') {
                    this.closeGalleryModal();
                }
            }
        });
    }

    handleSearch() {
        const formData = new FormData(document.getElementById('searchForm'));
        const searchData = {};

        // Convert FormData to object
        for (let [key, value] of formData.entries()) {
            if (key === 'user_name') {
                if (!searchData.user_names) searchData.user_names = [];
                if (value.trim()) searchData.user_names.push(value.trim());
            } else if (key === 'relative_size') {
                searchData.relative_size = true;
            } else if (value.trim()) {
                searchData[key] = value.trim();
            }
        }

        this.searchProjects(searchData);
    }

    populateUserNameDropdown() {
        const userNameFields = document.getElementById('user_name_fields');
        const select = userNameFields.querySelector('select');
        
        if (select) {
            // Clear existing options except the first empty one
            select.innerHTML = '<option value=""></option>';
            
            // Add user names
            this.userNames.forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = name;
                select.appendChild(option);
            });
        }
    }

    addUserNameDropdown() {
        const userNameFields = document.getElementById('user_name_fields');
        const label = document.createElement('label');
        label.innerHTML = 'User Name: ';
        
        const select = document.createElement('select');
        select.name = 'user_name';
        
        // Add empty option
        const emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        select.appendChild(emptyOpt);
        
        // Add user names
        this.userNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            select.appendChild(option);
        });
        
        label.appendChild(select);
        userNameFields.appendChild(label);
    }

    toggleCustomSize() {
        const paperSizeSelect = document.getElementById('paper_size_select');
        const customFields = document.getElementById('custom_size_fields');
        
        if (paperSizeSelect.value === 'custom') {
            customFields.style.display = 'block';
        } else {
            customFields.style.display = 'none';
        }
    }

    toggleRelativeSize() {
        const checkbox = document.getElementById('relative_size_checkbox');
        const percentDiv = document.getElementById('relative_size_percentages');
        
        if (checkbox && percentDiv) {
            if (checkbox.checked) {
                percentDiv.style.display = 'flex';
            } else {
                percentDiv.style.display = 'none';
            }
        }
    }

    resetForm() {
        document.getElementById('searchForm').reset();
        document.getElementById('custom_size_fields').style.display = 'none';
        document.getElementById('relative_size_percentages').style.display = 'none';
        
        // Clear additional user name dropdowns (keep only the first one)
        const userNamesDiv = document.getElementById('user_name_fields');
        const labels = userNamesDiv.querySelectorAll('label');
        for (let i = 1; i < labels.length; i++) {
            labels[i].remove();
        }
        
        // Reset the first user name dropdown
        if (labels.length > 0) {
            const firstSelect = labels[0].querySelector('select');
            if (firstSelect) {
                firstSelect.value = '';
            }
        }

        // Clear search results
        this.displaySearchResults([]);
    }

    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        
        if (!results || results.length === 0) {
            container.innerHTML = '<p>No matching projects found.</p>';
            return;
        }

        let html = `
            <h3>Project Results:</h3>
            <div class="table-container">
                <table border="1" cellpadding="5">
                    <tr>
                        <th>UUID</th>
                        <th>Project Name</th>
                        <th>User Name</th>
                        <th>Date</th>
                        <th>File Location</th>
                        <th>Paper Size</th>
                        <th>Description</th>
                        <th>Associated Scales</th>
                        <th class="actions-column">Actions</th>
                    </tr>
        `;

        results.forEach(proj => {
            if (proj && proj.uuid) {
                html += `
                    <tr>
                        <td>${this.escapeHtml(proj.uuid)}</td>
                        <td>${this.escapeHtml(proj.project_name)}</td>
                        <td>${this.escapeHtml(proj.user_name)}</td>
                        <td>${this.escapeHtml(proj.date)}</td>
                        <td>${this.escapeHtml(proj.file_location)}</td>
                        <td>${this.escapeHtml(proj.paper_size)}</td>
                        <td>${this.escapeHtml(proj.description)}</td>
                        <td>${this.escapeHtml(proj.associated_scales || 'N/A')}</td>
                        <td class="actions-column">
                            ${proj.view_file_path ? 
                                `<a href="#" onclick="app.showFileModal('${this.baseUrl}/view_file/${encodeURIComponent(proj.view_file_path)}','${proj.view_file_type}'); return false">View</a>` :
                                '<span>No file</span>'
                            }
                            <a href="#" onclick="app.copyPath('${this.escapeHtml(proj.file_location)}'); return false" style="background-color: #27ae60;">Copy Path</a>
                            <button type="button" onclick="app.deleteProject('${proj.uuid}')">Delete</button>
                        </td>
                    </tr>
                `;
            }
        });

        html += '</table></div>';
        container.innerHTML = html;
    }

    displayAllProjects(data) {
        const container = document.getElementById('all-projects');
        const projects = data.projects || [];
        const pagination = data.pagination || {};

        let html = `
            <h2>All Projects</h2>
            <div class="table-container">
                <table border="1" cellpadding="5">
                    <thead>
                        <tr>
                            <th>UUID <br> <input type="text" class="filter-input" data-filter="uuid_filter" placeholder="Filter UUID"></th>
                            <th>Project Name <br> <input type="text" class="filter-input" data-filter="project_name_filter" placeholder="Filter Name"></th>
                            <th>User Name <br> <input type="text" class="filter-input" data-filter="user_name_filter" placeholder="Filter User"></th>
                            <th>Date <br> <input type="text" class="filter-input" data-filter="date_filter" placeholder="Filter Date"></th>
                            <th>File Location <br> <input type="text" class="filter-input" data-filter="file_location_filter" placeholder="Filter Location"></th>
                            <th>Paper Size <br> <input type="text" class="filter-input" data-filter="paper_size_filter" placeholder="Filter Size"></th>
                            <th>Description</th>
                            <th>Associated Scales <br> <input type="text" class="filter-input" data-filter="associated_scales_filter" placeholder="Filter Scales"></th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        projects.forEach(proj => {
            if (proj && proj.uuid) {
                html += `
                    <tr>
                        <td>${this.escapeHtml(proj.uuid)}</td>
                        <td>${this.escapeHtml(proj.project_name)}</td>
                        <td>${this.escapeHtml(proj.user_name)}</td>
                        <td>${this.escapeHtml(proj.date)}</td>
                        <td>${this.escapeHtml(proj.file_location)}</td>
                        <td>${this.escapeHtml(proj.paper_size)}</td>
                        <td>${this.escapeHtml(proj.description)}</td>
                        <td>${this.escapeHtml(proj.associated_scales || 'N/A')}</td>
                        <td class="actions-column">
                            ${proj.view_file_path ? 
                                `<a href="#" onclick="app.showFileModal('${this.baseUrl}/view_file/${encodeURIComponent(proj.view_file_path)}','${proj.view_file_type}'); return false">View</a>` :
                                '<span>No file</span>'
                            }
                            <a href="#" onclick="app.copyPath('${this.escapeHtml(proj.file_location)}'); return false" style="background-color: #27ae60;">Copy Path</a>
                        </td>
                    </tr>
                `;
            }
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        // Add pagination
        if (pagination.total_pages > 1) {
            html += this.generatePagination(pagination, 'projects');
        }

        container.innerHTML = html;

        // Add event listeners to filter inputs
        container.querySelectorAll('.filter-input').forEach(input => {
            input.addEventListener('change', () => {
                this.applyProjectsTableFilters();
            });
            input.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.applyProjectsTableFilters();
                }
            });
        });
    }

    displayAllAreas(data) {
        const container = document.getElementById('all-areas');
        const areas = data.areas || [];
        const pagination = data.pagination || {};

        let html = `
            <h2>All Areas</h2>
            <div class="table-container">
                <table border="1" cellpadding="5">
                    <thead>
                        <tr>
                            <th>ID <br> <input type="text" class="areas-filter-input" data-filter="id_filter" placeholder="Filter ID"></th>
                            <th>Project UUID <br> <input type="text" class="areas-filter-input" data-filter="project_id_filter" placeholder="Filter UUID"></th>
                            <th>XMin <br> <input type="text" class="areas-filter-input" data-filter="xmin_filter" placeholder="Filter XMin"></th>
                            <th>YMin <br> <input type="text" class="areas-filter-input" data-filter="ymin_filter" placeholder="Filter YMin"></th>
                            <th>XMax <br> <input type="text" class="areas-filter-input" data-filter="xmax_filter" placeholder="Filter XMax"></th>
                            <th>YMax <br> <input type="text" class="areas-filter-input" data-filter="ymax_filter" placeholder="Filter YMax"></th>
                            <th>Scale <br> <input type="text" class="areas-filter-input" data-filter="scale_filter" placeholder="Filter Scale"></th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        areas.forEach(area => {
            html += `
                <tr>
                    <td>${area.id}</td>
                    <td>${this.escapeHtml(area.project_id)}</td>
                    <td>${area.xmin}</td>
                    <td>${area.ymin}</td>
                    <td>${area.xmax}</td>
                    <td>${area.ymax}</td>
                    <td>${area.scale}</td>
                    <td class="actions-column">
                        <a href="#" onclick="app.showFileModalOrNoFiles(${JSON.stringify(area.project_all_files).replace(/"/g, '&quot;')}); return false">View Project</a>
                        <a href="#" onclick="app.copyPath('${this.escapeHtml(area.project_file_location)}'); return false" style="background-color: #27ae60;">Copy Project Path</a>
                        <button type="button" onclick="app.copyTopRight('${area.xmax}', '${area.ymax}')">Copy Top Right</button>
                        <button type="button" onclick="app.copyBottomLeft('${area.xmin}', '${area.ymin}')">Copy Bottom Left</button>
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        // Add pagination
        if (pagination.total_pages > 1) {
            html += this.generatePagination(pagination, 'areas');
        }

        container.innerHTML = html;

        // Add event listeners to filter inputs
        container.querySelectorAll('.areas-filter-input').forEach(input => {
            input.addEventListener('change', () => {
                this.applyAreasTableFilters();
            });
            input.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    this.applyAreasTableFilters();
                }
            });
        });
    }

    generatePagination(pagination, type) {
        const { current_page, total_pages } = pagination;
        let html = '<div class="pagination">';

        // Previous button
        if (current_page > 1) {
            html += `<a href="#" onclick="app.loadAll${type.charAt(0).toUpperCase() + type.slice(1)}(${current_page - 1}); return false">Previous</a>`;
        } else {
            html += '<span class="disabled">Previous</span>';
        }

        // Page numbers
        for (let p = 1; p <= total_pages; p++) {
            if (p === current_page) {
                html += `<span class="current-page">${p}</span>`;
            } else {
                html += `<a href="#" onclick="app.loadAll${type.charAt(0).toUpperCase() + type.slice(1)}(${p}); return false">${p}</a>`;
            }
        }

        // Next button
        if (current_page < total_pages) {
            html += `<a href="#" onclick="app.loadAll${type.charAt(0).toUpperCase() + type.slice(1)}(${current_page + 1}); return false">Next</a>`;
        } else {
            html += '<span class="disabled">Next</span>';
        }

        html += '</div>';
        return html;
    }

    applyProjectsTableFilters() {
        const filters = {};
        document.querySelectorAll('#all-projects .filter-input').forEach(input => {
            if (input.value.trim()) {
                filters[input.dataset.filter] = input.value.trim();
            }
        });
        this.loadAllProjects(1, filters);
    }

    applyAreasTableFilters() {
        const filters = {};
        document.querySelectorAll('#all-areas .areas-filter-input').forEach(input => {
            if (input.value.trim()) {
                filters[input.dataset.filter] = input.value.trim();
            }
        });
        this.loadAllAreas(1, filters);
    }

    // Modal Methods
    showFileModal(url, type) {
        const modal = document.getElementById('fileModal');
        const body = document.getElementById('fileModalBody');
        
        if (type === 'pdf') {
            body.innerHTML = `<iframe src="${url}" width="800" height="600" style="border:none;"></iframe>`;
        } else if (type === 'img') {
            body.innerHTML = `<img src="${url}" style="max-width:80vw; max-height:80vh; display:block; margin:auto;" />`;
        }
        
        modal.style.display = 'flex';
    }

    closeFileModal() {
        const modal = document.getElementById('fileModal');
        const body = document.getElementById('fileModalBody');
        body.innerHTML = '';
        modal.style.display = 'none';
    }

    showFileModalOrNoFiles(files) {
        if (!files || files.length === 0) {
            const modal = document.getElementById('fileModal');
            const body = document.getElementById('fileModalBody');
            body.innerHTML = '<div style="text-align:center; padding:40px; font-size:1.2em; color:#888;">No files available for this project.</div>';
            modal.style.display = 'flex';
        } else if (files.length === 1) {
            const file = files[0];
            const url = `${this.baseUrl}/view_file/${encodeURIComponent(file.rel_path)}`;
            this.showFileModal(url, file.type);
        } else {
            // Multiple files: open gallery
            this.showGalleryModal(files);
        }
    }

    showGalleryModal(files) {
        this.currentFiles = files;
        this.currentFileIndex = 0;
        
        const modal = document.getElementById('galleryModal');
        const title = document.getElementById('galleryTitle');
        
        title.textContent = `Project Files (${files.length} files)`;
        modal.style.display = 'flex';
        
        this.displayCurrentFile();
    }

    closeGalleryModal() {
        const modal = document.getElementById('galleryModal');
        modal.style.display = 'none';
        this.currentFiles = [];
        this.currentFileIndex = 0;
    }

    displayCurrentFile() {
        if (this.currentFiles.length === 0) return;
        
        const file = this.currentFiles[this.currentFileIndex];
        const display = document.getElementById('galleryFileDisplay');
        const fileName = document.getElementById('fileName');
        const fileDate = document.getElementById('fileDate');
        const fileCounter = document.getElementById('fileCounter');
        const fileType = document.getElementById('fileType');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        
        // Update file info
        fileName.textContent = file.filename;
        fileDate.textContent = new Date(file.ctime * 1000).toLocaleString();
        fileCounter.textContent = `${this.currentFileIndex + 1} / ${this.currentFiles.length}`;
        fileType.textContent = file.type.toUpperCase();
        
        // Update navigation buttons
        prevBtn.style.display = this.currentFileIndex > 0 ? 'block' : 'none';
        nextBtn.style.display = this.currentFileIndex < this.currentFiles.length - 1 ? 'block' : 'none';
        
        // Generate URL dynamically
        const fileUrl = `${this.baseUrl}/view_file/${encodeURIComponent(file.rel_path)}`;
        
        // Display file content
        if (file.type === 'pdf') {
            display.innerHTML = `<iframe src="${fileUrl}" width="800" height="600" style="border:none; max-width:100%; max-height:100%;"></iframe>`;
        } else {
            display.innerHTML = `<img src="${fileUrl}" style="max-width:100%; max-height:100%; object-fit:contain;" alt="${file.filename}">`;
        }
    }

    previousFile() {
        if (this.currentFileIndex > 0) {
            this.currentFileIndex--;
            this.displayCurrentFile();
        }
    }

    nextFile() {
        if (this.currentFileIndex < this.currentFiles.length - 1) {
            this.currentFileIndex++;
            this.displayCurrentFile();
        }
    }

    // Utility Methods
    copyPath(path) {
        navigator.clipboard.writeText(path).then(() => {
            this.showCopyNotification('Path copied to clipboard!');
        }).catch(() => {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = path;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            this.showCopyNotification('Path copied to clipboard!');
        });
    }

    copyTopRight(xmax, ymax) {
        const str = `${xmax}/${ymax}`;
        this.copyToClipboard(str, `Top Right copied: ${str}`);
    }

    copyBottomLeft(xmin, ymin) {
        const str = `${xmin}/${ymin}`;
        this.copyToClipboard(str, `Bottom Left copied: ${str}`);
    }

    copyToClipboard(text, message) {
        navigator.clipboard.writeText(text).then(() => {
            this.showCopyNotification(message);
        }).catch(() => {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            this.showCopyNotification(message);
        });
    }

    showCopyNotification(message) {
        const notification = document.createElement('div');
        notification.textContent = message;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #27ae60; color: white; padding: 10px 15px; border-radius: 5px; z-index: 10000; font-size: 14px;';
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 2000);
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        } else {
            alert('Error: ' + message);
        }
    }

    showSuccess(message) {
        this.showCopyNotification(message);
    }

    showLoading(containerId, show) {
        const container = document.getElementById(containerId);
        if (!container) return;

        let loadingDiv = container.querySelector('.loading');
        if (!loadingDiv) {
            loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.textContent = 'Loading...';
            container.appendChild(loadingDiv);
        }

        loadingDiv.style.display = show ? 'block' : 'none';
    }

    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ArcSpatialDBClient();
});
