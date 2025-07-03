/**
 * Enhanced Teaching Content Database App
 * Features: Content CRUD, Tag Management, Interactive UI
 */

class App {
  constructor() {
    this.isLoading = false;
    this.currentPage = 'content';
    this.currentContent = null;
    this.currentFile = null;
    this.currentContentMode = 'text'; // 'text' or 'file'
    
    // Data storage
    this.allContent = [];
    this.allTags = [];
    this.allCategories = [];
    this.selectedTagIds = new Set();
    this.selectedCategoryIds = new Set();
    
    // Smart categorization
    this.smartCategorization = null;
    this.currentAnalysis = null;
    this.analysisTimeout = null;
    
    // Auto-upload handler (Task 2.2)
    this.autoUploadHandler = null;
    
    this.init();
  }

  async init() {
    this.setupEventListeners();
    this.setupTagInput();
    this.setupFileUploader();
    this.setupMobileMenu();
    this.setupQuickSelectButtons();
    
    // Initialize Smart Categorization
    this.smartCategorization = new SmartCategorization(this);
    
    // Initialize Auto-Upload Handler (Task 2.2)
    this.autoUploadHandler = new AutoUploadHandler(this);
    
    await this.loadInitialData();
    this.loadPageContent(this.currentPage);
  }

  setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const page = link.dataset.page;
        this.navigateTo(page);
      });
    });

    // Mobile menu toggle
    const menuToggle = document.getElementById('menu-toggle');
    if (menuToggle) {
      menuToggle.addEventListener('click', () => {
        this.toggleSidebar();
      });
    }

    // Search
    const searchInput = document.getElementById('search');
    if (searchInput) {
      let searchTimeout;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.performSearch(e.target.value);
        }, 300);
      });
    }

    // Add content button
    const addContentBtn = document.getElementById('add-content');
    if (addContentBtn) {
      addContentBtn.addEventListener('click', () => {
        this.showAddContentDialog();
      });
    }

    // Refresh button
    const refreshBtn = document.getElementById('refresh');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        this.refreshCurrentPage();
      });
    }

    // Action buttons
    document.addEventListener('click', (e) => {
      if (e.target.dataset.action) {
        this.handleAction(e.target.dataset.action, e.target.dataset);
      }
    });

    // Content form submission
    const contentForm = document.getElementById('content-form');
    if (contentForm) {
      contentForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleContentFormSubmit();
      });
    }

    // Tag input functionality
    this.setupTagInput();

    // File uploader functionality
    this.setupFileUploader();

    // Smart categorization triggers
    this.setupSmartCategorizationTriggers();

    // Modal close on background click
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('modal')) {
        this.closeModal(e.target.id);
      }
    });
  }

  setupTagInput() {
    const tagInput = document.getElementById('tag-input');
    if (tagInput) {
      let tagTimeout;
      tagInput.addEventListener('input', (e) => {
        clearTimeout(tagTimeout);
        tagTimeout = setTimeout(() => {
          this.handleTagInput(e.target.value);
        }, 200);
      });

      tagInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const suggestions = document.getElementById('tag-suggestions');
          const firstSuggestion = suggestions.querySelector('.tag-suggestion');
          if (firstSuggestion) {
            firstSuggestion.click();
          }
        }
      });
    }
  }

  setupFileUploader() {
    // Content type toggle buttons
    const textContentBtn = document.getElementById('text-content-btn');
    const fileContentBtn = document.getElementById('file-content-btn');
    
    if (textContentBtn && fileContentBtn) {
      textContentBtn.addEventListener('click', () => this.switchContentMode('text'));
      fileContentBtn.addEventListener('click', () => this.switchContentMode('file'));
    }

    // File input and drop zone
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('file-drop-zone');
    const browseBtn = dropZone?.querySelector('.file-browse-btn');
    const replaceBtn = document.getElementById('file-current-replace');

    if (fileInput && dropZone) {
      // File input change
      fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
          this.handleFileSelect(e.target.files[0]);
        }
      });

      // Browse button click
      if (browseBtn) {
        browseBtn.addEventListener('click', (e) => {
          e.preventDefault();
          fileInput.click();
        });
      }

      // Drop zone click
      dropZone.addEventListener('click', () => {
        fileInput.click();
      });

      // Drag and drop events
      dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.parentElement.classList.add('drag-over');
      });

      dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        if (!dropZone.contains(e.relatedTarget)) {
          dropZone.parentElement.classList.remove('drag-over');
        }
      });

      dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.parentElement.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
          this.handleFileSelect(files[0]);
        }
      });
    }

    // Replace button
    if (replaceBtn) {
      replaceBtn.addEventListener('click', () => {
        if (fileInput) {
          fileInput.click();
        }
      });
    }
  }

  switchContentMode(mode) {
    this.currentContentMode = mode;
    
    // Update button states
    const textBtn = document.getElementById('text-content-btn');
    const fileBtn = document.getElementById('file-content-btn');
    const textSection = document.getElementById('text-content-section');
    const fileSection = document.getElementById('file-content-section');

    if (textBtn && fileBtn && textSection && fileSection) {
      // Update button appearance
      textBtn.classList.toggle('active', mode === 'text');
      fileBtn.classList.toggle('active', mode === 'file');

      // Update section visibility
      textSection.classList.toggle('active', mode === 'text');
      fileSection.classList.toggle('active', mode === 'file');
    }

    // Clear current file if switching to text mode
    if (mode === 'text') {
      this.clearCurrentFile();
    }
  }

  handleFileSelect(file) {
    // Validate file
    const validation = this.validateFile(file);
    if (!validation.valid) {
      this.showToast(validation.message, 'error');
      return;
    }

    // Store file
    this.currentFile = file;
    
    // Update UI
    this.updateFileDisplay(file);
    
    console.log('File selected:', file.name, file.size, file.type);
    
    // Trigger smart categorization analysis
    this.triggerSmartAnalysis();
  }

  validateFile(file) {
    // Check file size (16MB limit)
    const maxSize = 16 * 1024 * 1024;
    if (file.size > maxSize) {
      return {
        valid: false,
        message: 'File is too large. Maximum size is 16MB.'
      };
    }

    // Check file type
    const allowedTypes = [
      // Documents
      '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
      // Presentations
      '.ppt', '.pptx', '.odp',
      // Spreadsheets
      '.xls', '.xlsx', '.ods', '.csv',
      // Images
      '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg',
      // Audio
      '.mp3', '.wav', '.ogg', '.m4a',
      // Video
      '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
      // Archives
      '.zip', '.rar', '.7z', '.tar', '.gz'
    ];

    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
      return {
        valid: false,
        message: 'File type not supported. Please select a document, image, audio, video, or archive file.'
      };
    }

    return { valid: true };
  }

  updateFileDisplay(file) {
    const dropZone = document.getElementById('file-drop-zone');
    const currentFile = document.getElementById('file-current');
    const currentIcon = document.getElementById('file-current-icon');
    const currentName = document.getElementById('file-current-name');
    const currentMeta = document.getElementById('file-current-meta');

    if (dropZone && currentFile && currentIcon && currentName && currentMeta) {
      // Hide drop zone, show current file
      dropZone.style.display = 'none';
      currentFile.classList.remove('hidden');

      // Update file info
      currentIcon.textContent = this.getFileIcon(file.name);
      currentName.textContent = file.name;
      currentMeta.textContent = `${this.formatFileSize(file.size)} • ${this.getFileType(file.name)}`;
    }
  }

  clearCurrentFile() {
    this.currentFile = null;
    
    const dropZone = document.getElementById('file-drop-zone');
    const currentFile = document.getElementById('file-current');
    const fileInput = document.getElementById('file-input');

    if (dropZone && currentFile) {
      dropZone.style.display = 'block';
      currentFile.classList.add('hidden');
    }

    if (fileInput) {
      fileInput.value = '';
    }
  }

  getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    
    // Document types
    if (['pdf'].includes(ext)) return '📄';
    if (['doc', 'docx', 'txt', 'rtf', 'odt'].includes(ext)) return '📝';
    if (['ppt', 'pptx', 'odp'].includes(ext)) return '📊';
    if (['xls', 'xlsx', 'ods', 'csv'].includes(ext)) return '📈';
    
    // Media types
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(ext)) return '🖼️';
    if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return '🎵';
    if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(ext)) return '🎬';
    
    // Archive types
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return '📦';
    
    return '📎';
  }

  getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    
    if (['pdf'].includes(ext)) return 'PDF Document';
    if (['doc', 'docx'].includes(ext)) return 'Word Document';
    if (['txt', 'rtf'].includes(ext)) return 'Text Document';
    if (['ppt', 'pptx'].includes(ext)) return 'Presentation';
    if (['xls', 'xlsx'].includes(ext)) return 'Spreadsheet';
    if (['csv'].includes(ext)) return 'CSV File';
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp'].includes(ext)) return 'Image';
    if (['svg'].includes(ext)) return 'Vector Image';
    if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return 'Audio';
    if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(ext)) return 'Video';
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'Archive';
    
    return ext.toUpperCase() + ' File';
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  showUploadProgress(progress) {
    const progressElement = document.getElementById('file-upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const dropZone = document.getElementById('file-drop-zone');
    const currentFile = document.getElementById('file-current');

    if (progressElement && progressFill && progressText) {
      if (progress === 0) {
        // Show progress, hide other elements
        dropZone?.style.setProperty('display', 'none');
        currentFile?.classList.add('hidden');
        progressElement.classList.remove('hidden');
      }

      // Update progress
      progressFill.style.width = `${progress}%`;
      progressText.textContent = progress < 100 ? `Uploading... ${progress}%` : 'Processing...';

      if (progress >= 100) {
        // Hide progress after a delay
        setTimeout(() => {
          progressElement.classList.add('hidden');
        }, 1000);
      }
    }
  }

  setupMobileMenu() {
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 768 && this.sidebarOpen) {
        const sidebar = document.getElementById('sidebar');
        const menuToggle = document.getElementById('menu-toggle');
        
        if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
          this.closeSidebar();
        }
      }
    });

    // Close sidebar on window resize
    window.addEventListener('resize', () => {
      if (window.innerWidth > 768) {
        this.closeSidebar();
      }
    });
  }

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen;
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open', this.sidebarOpen);
  }

  closeSidebar() {
    this.sidebarOpen = false;
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('open');
  }

  navigateTo(page) {
    // Update active navigation
    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-page="${page}"]`);
    if (activeLink) {
      activeLink.classList.add('active');
    }

    // Update page title
    const pageTitle = document.getElementById('page-title');
    if (pageTitle) {
      pageTitle.textContent = this.getPageTitle(page);
    }

    // Update current page
    this.currentPage = page;

    // Load page content
    this.loadPageContent(page);

    // Close mobile sidebar
    if (window.innerWidth <= 768) {
      this.closeSidebar();
    }
  }

  getPageTitle(page) {
    const titles = {
      dashboard: 'Dashboard'
    };
    return titles[page] || 'Dashboard';
  }

  async loadPageContent(page) {
    const content = document.getElementById('page-content');
    if (!content) return;

    this.showLoading();

    try {
      switch (page) {
        case 'content':
        case 'dashboard':
        default:
          await this.getContentPageContent();
          break;
      }
    } catch (error) {
      console.error('Error loading page content:', error);
      content.innerHTML = `
        <div class="welcome">
          <h3>Error loading page content</h3>
          <p>There was a problem loading the page. Please refresh and try again.</p>
          <div class="actions">
            <button class="btn-primary" onclick="location.reload()">Refresh Page</button>
          </div>
        </div>
      `;
      this.showToast('Error loading page content', 'error');
    } finally {
      this.hideLoading();
    }
  }

  async getContentPageContent() {
    try {
      await this.loadAllContent();
      await this.loadAllTags();
      await this.loadAllCategories();
      
      // Create auto-upload UI for content page
      if (this.autoUploadHandler) {
        this.autoUploadHandler.createAutoUploadUI();
      }
      
      // Check if we have content to display
      if (this.allContent.length === 0) {
        return `
          <div class="welcome">
            <h3>Welcome to your Teaching Content Database</h3>
            <p>Start by adding your first piece of teaching content to get organized.</p>
            <div class="actions">
              <button class="btn-primary large" onclick="app.handleAction('add-content')">Add Your First Content</button>
            </div>
          </div>
        `;
      }
      
      let html = `
        <div class="content-page">
          <div class="tag-filter-bar" id="tag-filter-bar">
            <!-- Tag filter bar will be populated -->
          </div>
          
          <div class="content-main-area">
            <div class="content-list-container">
              <div class="actions">
                <div class="content-count">
                  <span id="content-count-display">${this.allContent.length} items</span>
                </div>
                <button class="btn-primary" onclick="app.handleAction('add-content')">
                  Add Content
                </button>
              </div>
              
              <div class="content-grid" id="content-grid">
                <!-- Content items will be populated here -->
              </div>
            </div>
            
            <div class="category-filter-sidebar" id="category-filter-sidebar">
              <!-- Category filters will be populated -->
            </div>
          </div>
        </div>
      `;
      
      // Set the content
      document.querySelector('.page-content').innerHTML = html;
      
      // Initialize components
      this.renderTagFilterBar();
      this.renderCategoryFilterSidebar();
      this.displayFilteredContent(this.allContent);
      this.updateContentCount();
      
      // Re-setup auto-upload after content is rendered
      if (this.autoUploadHandler) {
        this.autoUploadHandler.setupDropZone();
      }
      
      return html;
      
    } catch (error) {
      console.error('Error loading content page:', error);
      return `
        <div class="welcome">
          <h3>Error loading content</h3>
          <p>There was a problem loading your content. Please check the server connection and try again.</p>
          <div class="actions">
            <button class="btn-primary" onclick="app.refreshCurrentPage()">Retry</button>
          </div>
        </div>
      `;
    }
  }

  renderContentItem(item) {
    const tags = (item.tags || []).map(tag => 
      `<span class="content-tag ${tag.color ? 'colored' : ''}" ${tag.color ? `style="background-color: ${tag.color}"` : ''}>${tag.name}</span>`
    ).join('');

    const meta = [
      item.content_type ? `Type: ${item.content_type}` : null,
      item.subject ? `Subject: ${item.subject}` : null,
      item.grade_level ? `Grade: ${item.grade_level}` : null,
      item.duration ? `Duration: ${item.duration}min` : null
    ].filter(Boolean).join(' • ');

    // Add file indicator if content has a file
    const fileIndicator = item.file_path && item.original_filename ? 
      `<span class="content-item-file-indicator">
         ${this.getFileIcon(item.original_filename)} ${this.getFileType(item.original_filename)}
       </span>` : '';

    return `
      <div class="content-item" onclick="app.viewContent(${item.id})">
        <div class="content-item-header">
          <h4 class="content-item-title">
            ${item.title || 'Untitled'}
            ${fileIndicator}
          </h4>
          <div class="content-item-actions" onclick="event.stopPropagation()">
            <button class="content-item-action edit" onclick="app.editContent(${item.id})" data-action="edit-content" data-id="${item.id}">Edit</button>
            <button class="content-item-action delete" onclick="app.deleteContent(${item.id})" data-action="delete-content" data-id="${item.id}">Delete</button>
          </div>
        </div>
        ${meta ? `<div class="content-item-meta">${meta}</div>` : ''}
        <div class="content-item-description">${item.description || 'No description'}</div>
        <div class="content-item-tags">${tags}</div>
      </div>
    `;
  }

  renderTagFilterBar() {
    const tags = this.allTags || [];
    
    if (tags.length === 0) {
      document.getElementById('tag-filter-bar').innerHTML = '<div class="no-tags">No tags available</div>';
      return;
    }

    const tagChips = tags.map(tag => {
      const isSelected = this.selectedTagIds.has(tag.id);
      return `
        <div class="filter-tag-chip ${isSelected ? 'selected' : ''} ${tag.color ? 'colored' : ''}" 
             ${tag.color ? `style="--tag-color: ${tag.color}"` : ''}
             onclick="app.toggleTagFilter(${tag.id})" 
             data-tag-id="${tag.id}">
          ${tag.name} 
          <span class="tag-count">${tag.usage_count || 0}</span>
        </div>
      `;
    }).join('');

    const filterBarHTML = `
      <div class="tag-filter-header">
        <h4>Filter by Tags</h4>
        ${this.selectedTagIds.size > 0 ? 
          `<button class="clear-filters-btn" onclick="app.clearAllFilters()">Clear All (${this.selectedTagIds.size})</button>` : 
          ''
        }
      </div>
      <div class="tag-chips-container">
        ${tagChips}
      </div>
    `;

    document.getElementById('tag-filter-bar').innerHTML = filterBarHTML;
  }

  toggleTagFilter(tagId) {
    if (this.selectedTagIds.has(tagId)) {
      this.selectedTagIds.delete(tagId);
    } else {
      this.selectedTagIds.add(tagId);
    }
    
    this.updateTagFilterDisplay();
    this.filterContentByTagsAndCategories();
  }

  clearAllFilters() {
    this.selectedTagIds.clear();
    this.updateTagFilterDisplay();
    this.filterContentByTagsAndCategories();
  }

  updateTagFilterDisplay() {
    // Update tag chip appearances
    document.querySelectorAll('.filter-tag-chip').forEach(chip => {
      const tagId = parseInt(chip.dataset.tagId);
      chip.classList.toggle('selected', this.selectedTagIds.has(tagId));
    });

    // Update clear button
    const tagFilterBar = document.querySelector('.tag-filter-bar');
    if (tagFilterBar) {
      const header = tagFilterBar.querySelector('.tag-filter-header');
      const clearBtn = header.querySelector('.clear-filters-btn');
      
      if (this.selectedTagIds.size > 0) {
        if (!clearBtn) {
          header.innerHTML += ` <button class="clear-filters-btn" onclick="app.clearAllFilters()">Clear All (${this.selectedTagIds.size})</button>`;
        } else {
          clearBtn.textContent = `Clear All (${this.selectedTagIds.size})`;
        }
      } else if (clearBtn) {
        clearBtn.remove();
      }
    }
  }

  filterContentByTagsAndCategories() {
    let filteredContent = this.allContent;

    // Apply tag filter (OR logic for tags)
    if (this.selectedTagIds.size > 0) {
      filteredContent = filteredContent.filter(item => {
        const itemTagIds = (item.tags || []).map(tag => tag.id);
        return Array.from(this.selectedTagIds).some(tagId => itemTagIds.includes(tagId));
      });
    }

    // Phase 3A.1: Fixed subject-based filtering (was broken category_id filtering)
    if (this.selectedCategoryIds.size > 0) {
      const selectedSubjects = Array.from(this.selectedCategoryIds).map(categoryId => {
        const category = this.allCategories.find(cat => cat.id === categoryId);
        return category ? category.name : null;
      }).filter(Boolean);
      
      console.log(`🔍 Filtering by subjects: [${selectedSubjects.join(', ')}]`);
      
      filteredContent = filteredContent.filter(item => {
        // Match by subject name instead of category_id
        const matches = selectedSubjects.some(subjectName => 
          item.subject === subjectName || item.subject_name === subjectName
        );
        
        if (matches) {
          console.log(`✅ Content "${item.title}" matches subject "${item.subject}"`);
        }
        
        return matches;
      });
      
      console.log(`📊 Filtered result: ${filteredContent.length} items`);
    }

    this.displayFilteredContent(filteredContent);
  }

  displayFilteredContent(content) {
    const contentList = document.getElementById('content-grid');
    const countElement = document.getElementById('content-count-display');
    
    if (contentList) {
      if (content.length === 0) {
        const hasTagFilters = this.selectedTagIds.size > 0;
        const hasCategoryFilters = this.selectedCategoryIds.size > 0;
        
        let clearOptions = '';
        if (hasTagFilters && hasCategoryFilters) {
          clearOptions = `<button class="link-btn" onclick="app.clearAllFilters()">clear tag filters</button> or <button class="link-btn" onclick="app.clearAllCategoryFilters()">clear category filters</button>`;
        } else if (hasTagFilters) {
          clearOptions = `<button class="link-btn" onclick="app.clearAllFilters()">clear tag filters</button>`;
        } else if (hasCategoryFilters) {
          clearOptions = `<button class="link-btn" onclick="app.clearAllCategoryFilters()">clear category filters</button>`;
        } else {
          clearOptions = `<button class="link-btn" onclick="app.clearAllFilters(); app.clearAllCategoryFilters();">clear all filters</button>`;
        }
        
        contentList.innerHTML = `
          <div class="no-results">
            <h4>No content matches your filter</h4>
            <p>Try selecting different options or ${clearOptions}.</p>
          </div>
        `;
      } else {
        contentList.innerHTML = content.map(item => this.renderContentItem(item)).join('');
      }
    }
    
    if (countElement) {
      countElement.textContent = `${content.length} items`;
    }
  }

  renderCategoryFilterSidebar() {
    const categories = this.allCategories || [];
    const sidebar = document.getElementById('category-filter-sidebar');
    
    if (!sidebar) return;
    
    if (categories.length === 0) {
      sidebar.innerHTML = `
        <div class="category-filter-header">
          <h4>Subjects</h4>
        </div>
        <div class="no-categories">No subjects available</div>
      `;
      return;
    }

    const categoryCheckboxes = categories.map(category => {
      const isSelected = this.selectedCategoryIds.has(category.id);
      const contentCount = this.getCategoryContentCount(category.id);
      
      return `
        <div class="category-checkbox-item">
          <label class="category-checkbox-label">
            <div class="checkbox-container">
              <input 
                type="checkbox" 
                class="category-checkbox" 
                ${isSelected ? 'checked' : ''}
                onchange="app.toggleCategoryFilter(${category.id})"
                data-category-id="${category.id}"
              >
              <span class="category-checkbox-text">${category.name}</span>
            </div>
            <span class="category-content-count">${contentCount}</span>
          </label>
        </div>
      `;
    }).join('');

    sidebar.innerHTML = `
      <div class="category-filter-header">
        <h4>Subjects</h4>
        ${this.selectedCategoryIds.size > 0 ? 
          `<button class="clear-category-filters-btn" onclick="app.clearAllCategoryFilters()">Clear All (${this.selectedCategoryIds.size})</button>` : 
          ''
        }
      </div>
      <div class="category-checkboxes">
        ${categoryCheckboxes}
      </div>
    `;
  }

  getCategoryContentCount(categoryId) {
    // Phase 3A.3: Use server-provided counts when available, fallback to subject-based counting
    const category = this.allCategories.find(cat => cat.id === categoryId);
    
    if (category && typeof category.content_count === 'number') {
      // Use server-provided count (more accurate and efficient)
      return category.content_count;
    }
    
    // Fallback: client-side subject-based counting (fixed logic)
    if (!this.allContent || !category) return 0;
    return this.allContent.filter(item => 
      item.subject === category.name || item.subject_name === category.name
    ).length;
  }

  toggleCategoryFilter(categoryId) {
    if (this.selectedCategoryIds.has(categoryId)) {
      this.selectedCategoryIds.delete(categoryId);
    } else {
      this.selectedCategoryIds.add(categoryId);
    }
    
    this.updateCategoryFilterDisplay();
    this.filterContentByTagsAndCategories();
  }

  clearAllCategoryFilters() {
    this.selectedCategoryIds.clear();
    this.updateCategoryFilterDisplay();
    this.filterContentByTagsAndCategories();
  }

  updateCategoryFilterDisplay() {
    // Update checkbox states
    document.querySelectorAll('.category-checkbox').forEach(checkbox => {
      const categoryId = parseInt(checkbox.dataset.categoryId);
      checkbox.checked = this.selectedCategoryIds.has(categoryId);
    });

    // Update clear button
    const sidebar = document.querySelector('.category-filter-sidebar');
    if (sidebar) {
      const header = sidebar.querySelector('.category-filter-header');
      const clearBtn = header.querySelector('.clear-category-filters-btn');
      
      if (this.selectedCategoryIds.size > 0) {
        if (!clearBtn) {
          header.innerHTML += ` <button class="clear-category-filters-btn" onclick="app.clearAllCategoryFilters()">Clear All (${this.selectedCategoryIds.size})</button>`;
        } else {
          clearBtn.textContent = `Clear All (${this.selectedCategoryIds.size})`;
        }
      } else if (clearBtn) {
        clearBtn.remove();
      }
    }
  }

  async loadInitialData() {
    try {
      // Load tags and categories for form dropdowns
      await Promise.all([
        this.loadAllTags(),
        this.loadAllCategories()
      ]);

      // Test API connection
      const response = await fetch('/api/health');
      if (response.ok) {
        this.updateConnectionStatus(true);
      } else {
        this.updateConnectionStatus(false);
      }
    } catch (error) {
      console.warn('API connection failed:', error);
      this.updateConnectionStatus(false);
    }
  }

  async loadAllTags() {
    try {
      const response = await fetch('/api/tags');
      const data = await response.json();
      this.allTags = data.data || [];
    } catch (error) {
      console.warn('Failed to load tags:', error);
      this.allTags = [];
    }
  }

  async loadAllCategories() {
    try {
      // Phase 3A.2: Use enhanced API endpoint that includes content counts
      const response = await fetch('/api/categories');
      const data = await response.json();
      this.allCategories = data.data || [];
      
      // Log successful loading with enhanced data
      console.log(`✅ Loaded ${this.allCategories.length} subjects with content counts:`, 
        this.allCategories.map(cat => `${cat.name} (${cat.content_count || 0})`).join(', '));
    } catch (error) {
      console.warn('Failed to load categories:', error);
      this.allCategories = [];
    }
  }

  async loadAllContent() {
    try {
      const response = await fetch('/api/content');
      const data = await response.json();
      this.allContent = data.data || [];
      
      // Clear selected filters when loading new content
      this.selectedTagIds = new Set();
      this.selectedCategoryIds = new Set();
      
      console.log(`✅ Loaded ${this.allContent.length} content items`);
    } catch (error) {
      console.warn('Failed to load content:', error);
      this.allContent = [];
    }
  }

  // Phase 3A.2: Alternative enhanced subjects loading method
  async loadAllSubjects() {
    try {
      const response = await fetch('/api/subjects');
      const data = await response.json();
      this.allCategories = data.data || []; // Store in same variable for compatibility
      
      console.log(`✅ Loaded ${this.allCategories.length} subjects from enhanced API:`, 
        this.allCategories.map(cat => `${cat.name} (${cat.content_count || 0})`).join(', '));
    } catch (error) {
      console.warn('Enhanced subjects API not available, using categories:', error);
      // Fallback to regular categories API
      await this.loadAllCategories();
    }
  }

  updateContentCount() {
    // Update navigation badge with current content count
    const contentBadge = document.getElementById('content-count');
    if (contentBadge && this.allContent) {
      contentBadge.textContent = this.allContent.length;
    }
  }

  updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    
    if (statusDot && statusText) {
      if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Connected';
      } else {
        statusDot.classList.remove('connected');
        statusText.textContent = 'Connection Error';
      }
    }
  }

  // Content Management Functions
  async viewContent(contentId) {
    try {
      const response = await fetch(`/api/content/${contentId}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.currentContent = data.data;
        this.showContentViewer(data.data);
      } else {
        this.showToast('Error loading content details', 'error');
      }
    } catch (error) {
      console.error('Error viewing content:', error);
      this.showToast('Error loading content details', 'error');
    }
  }

  showContentViewer(content) {
    const modal = document.getElementById('content-modal');
    const title = document.getElementById('modal-title');
    const body = document.getElementById('content-modal-body');

    title.textContent = content.title || 'Content Details';

    const tags = (content.tags || []).map(tag => 
      `<span class="content-tag ${tag.color ? 'colored' : ''}" ${tag.color ? `style="background-color: ${tag.color}"` : ''}>${tag.name}</span>`
    ).join('');

    body.innerHTML = `
      <div class="content-viewer">
        <div class="content-viewer-header">
          <h3 class="content-viewer-title">${content.title || 'Untitled'}</h3>
          <div class="content-viewer-meta">
            <div class="content-viewer-meta-item">
              <div class="content-viewer-meta-label">Type</div>
              <div class="content-viewer-meta-value">${content.content_type || 'N/A'}</div>
            </div>
            <div class="content-viewer-meta-item">
              <div class="content-viewer-meta-label">Subject</div>
              <div class="content-viewer-meta-value">${content.subject || 'N/A'}</div>
            </div>
            <div class="content-viewer-meta-item">
              <div class="content-viewer-meta-label">Grade Level</div>
              <div class="content-viewer-meta-value">${content.grade_level || 'N/A'}</div>
            </div>

            <div class="content-viewer-meta-item">
              <div class="content-viewer-meta-label">Duration</div>
              <div class="content-viewer-meta-value">${content.duration ? content.duration + ' min' : 'N/A'}</div>
            </div>
            <div class="content-viewer-meta-item">
              <div class="content-viewer-meta-label">Status</div>
              <div class="content-viewer-meta-value">${content.status || 'active'}</div>
            </div>
          </div>
          <div class="content-item-tags">${tags}</div>
        </div>
        <div class="content-viewer-body">
          ${content.description ? `
            <div class="content-viewer-section">
              <div class="content-viewer-section-title">Description</div>
              <div class="content-viewer-text">${content.description}</div>
            </div>
          ` : ''}
          
          ${this.renderFileDownloadSection(content)}
          
          ${content.content ? `
            <div class="content-viewer-section">
              <div class="content-viewer-section-title">Content</div>
              <div class="content-viewer-text">${content.content}</div>
            </div>
          ` : ''}
          ${content.keywords ? `
            <div class="content-viewer-section">
              <div class="content-viewer-section-title">Keywords</div>
              <div class="content-viewer-text">${content.keywords}</div>
            </div>
          ` : ''}
        </div>
        <div class="form-actions">
          <button class="btn-primary" onclick="app.editContent(${content.id})">Edit Content</button>
          <button class="btn-danger" onclick="app.deleteContent(${content.id})">Delete Content</button>
        </div>
      </div>
    `;

    this.showModal('content-modal');
  }

  renderFileDownloadSection(content) {
    // Check if content has a file
    if (!content.file_path || !content.original_filename) {
      return '';
    }

    const fileIcon = this.getFileIcon(content.original_filename);
    const fileType = this.getFileType(content.original_filename);
    const fileSize = content.file_size ? this.formatFileSize(content.file_size) : 'Unknown size';
    const fileTypeBadgeClass = this.getFileTypeBadgeClass(content.original_filename);

    return `
      <div class="file-download-section">
        <div class="file-download-header">
          <div class="file-download-icon">${fileIcon}</div>
          <div class="file-download-info">
            <h4>${content.original_filename}</h4>
            <div class="file-download-meta">${fileSize} • ${fileType}</div>
          </div>
        </div>
        <div class="file-download-actions">
          <a href="/api/content/${content.id}/download" class="file-download-btn" target="_blank">
            📥 Download File
          </a>
          <span class="file-type-badge ${fileTypeBadgeClass}">${fileType}</span>
        </div>
      </div>
    `;
  }

  getFileTypeBadgeClass(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    
    if (['pdf'].includes(ext)) return 'pdf';
    if (['doc', 'docx', 'txt', 'rtf', 'odt'].includes(ext)) return 'doc';
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].includes(ext)) return 'image';
    if (['mp3', 'wav', 'ogg', 'm4a'].includes(ext)) return 'audio';
    if (['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'].includes(ext)) return 'video';
    
    return '';
  }

  async editContent(contentId) {
    try {
      const response = await fetch(`/api/content/${contentId}`);
      const data = await response.json();
      
      if (data.status === 'success') {
        this.currentContent = data.data;
        this.showAddContentDialog(data.data);
      } else {
        this.showToast('Error loading content for editing', 'error');
      }
    } catch (error) {
      console.error('Error loading content for editing:', error);
      this.showToast('Error loading content for editing', 'error');
    }
  }

  async deleteContent(contentId) {
    this.showConfirmDialog(
      'Are you sure you want to delete this content? This action cannot be undone.',
      async () => {
        try {
          const response = await fetch(`/api/content/${contentId}`, {
            method: 'DELETE'
          });
          
          const data = await response.json();
          
          if (data.status === 'success') {
            this.showToast('Content deleted successfully', 'success');
            this.refreshCurrentPage();
            this.closeModal('content-modal');
          } else {
            this.showToast('Error deleting content', 'error');
          }
        } catch (error) {
          console.error('Error deleting content:', error);
          this.showToast('Error deleting content', 'error');
        }
      }
    );
  }

  async showAddContentDialog(editContent = null) {
    const modal = document.getElementById('add-content-modal');
    const title = document.getElementById('add-content-title');
    const form = document.getElementById('content-form');
    
    // Set modal title
    title.textContent = editContent ? 'Edit Content' : 'Add Content';
    
    // Phase 4A: Load harmonized subjects into dropdown (replace category logic)
    const subjectSelect = document.getElementById('content-subject');
    subjectSelect.innerHTML = '<option value="">Select subject</option>';
    this.allCategories.forEach(category => {
      const option = document.createElement('option');
      option.value = category.name; // Use subject name instead of ID
      option.textContent = category.name;
      subjectSelect.appendChild(option);
    });
    
    console.log(`📝 Loaded ${this.allCategories.length} subjects into form dropdown`);

    // Setup quick-select buttons
    this.setupQuickSelectButtons();

    // Fill form if editing
    if (editContent) {
      document.getElementById('content-title').value = editContent.title || '';
      // document.getElementById('content-type').value = editContent.content_type || '';  // Removed - using tags
      document.getElementById('content-subject').value = editContent.subject || ''; // Now dropdown with subject name
      document.getElementById('content-grade').value = editContent.grade_level || '';
      document.getElementById('content-duration').value = editContent.duration || '';
      document.getElementById('content-description').value = editContent.description || '';
      document.getElementById('content-body').value = editContent.content || '';
      document.getElementById('content-keywords').value = editContent.keywords || '';
      // Phase 4A: Removed category_id field - using subject dropdown instead
      
      // Determine content mode based on whether content has a file
      if (editContent.file_path && editContent.original_filename) {
        this.switchContentMode('file');
        // Show current file info for editing
        this.updateFileDisplay({
          name: editContent.original_filename,
          size: editContent.file_size || 0,
          type: editContent.mime_type || 'application/octet-stream'
        });
        // Don't require a new file when editing file content
        this.currentFile = { placeholder: true };
      } else {
        this.switchContentMode('text');
      }
      
      // Set selected tags
      this.selectedTagIds.clear();
      if (editContent.tags) {
        editContent.tags.forEach(tag => {
          this.selectedTagIds.add(tag.id);
        });
        this.updateSelectedTags();
        this.updateQuickSelectButtons();
      }
    } else {
      form.reset();
      this.selectedTagIds.clear();
      this.updateSelectedTags();
      this.updateQuickSelectButtons();
      this.switchContentMode('text');
      this.clearCurrentFile();
    }

    this.showModal('add-content-modal');
  }

  async handleContentFormSubmit() {
    try {
      // Validate required fields
      const title = document.getElementById('content-title')?.value;
      const subject = document.getElementById('content-subject')?.value;
      
      if (!title || !subject) {
        this.showToast('Please fill in all required fields', 'error');
        return;
      }

      // Check content mode and validate accordingly
      if (this.currentContentMode === 'file' && !this.currentFile && !this.currentContent) {
        this.showToast('Please select a file to upload', 'error');
        return;
      }

      this.showLoading();
      
      let response;
      let contentId;

      if (this.currentContentMode === 'file' && this.currentFile) {
        // File upload mode
        response = await this.uploadFile();
        if (response && response.status === 'success') {
          contentId = response.data.id;
        }
      } else {
        // Text content mode or updating existing content
        const form = document.getElementById('content-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Add duration as number
        if (data.duration) {
          data.duration = parseInt(data.duration);
        }

        const isEdit = this.currentContent && this.currentContent.id;
        const url = isEdit ? `/api/content/${this.currentContent.id}` : '/api/content';
        const method = isEdit ? 'PUT' : 'POST';

        response = await fetch(url, {
          method: method,
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.status === 'success') {
          contentId = isEdit ? this.currentContent.id : result.data.id;
        }
      }

      if (response && (response.status === 'success' || response.ok)) {
        // Handle tag assignment if content was created/updated successfully
        if (contentId && this.selectedTagIds.size > 0) {
          await this.assignTagsToContent(contentId, Array.from(this.selectedTagIds));
        }

        this.showToast(
          this.currentContent ? 'Content updated successfully' : 'Content created successfully',
          'success'
        );
        
        this.closeModal('add-content-modal');
        this.refreshCurrentPage();
        this.currentContent = null;
        
        // Reset file uploader state
        this.currentContentMode = 'text';
        this.clearCurrentFile();
        this.switchContentMode('text');
      } else {
        const result = response.status ? response : await response.json();
        this.showToast(result.message || 'An error occurred', 'error');
      }
      
    } catch (error) {
      console.error('Error submitting form:', error);
      this.showToast('An error occurred while saving content', 'error');
    } finally {
      this.hideLoading();
    }
  }

  async uploadFile() {
    if (!this.currentFile) {
      throw new Error('No file selected');
    }

    const formData = new FormData();
    
    // Add file
    formData.append('file', this.currentFile);
    
    // Add form fields
    const form = document.getElementById('content-form');
    const titleInput = form.querySelector('[name="title"]');
    const subjectInput = form.querySelector('[name="subject"]');
    const descriptionInput = form.querySelector('[name="description"]');
    const gradeLevelInput = form.querySelector('[name="grade_level"]');
    const durationInput = form.querySelector('[name="duration"]');
    const keywordsInput = form.querySelector('[name="keywords"]');
    
    if (titleInput?.value) formData.append('title', titleInput.value);
    if (subjectInput?.value) formData.append('subject', subjectInput.value);
    if (descriptionInput?.value) formData.append('description', descriptionInput.value);
    if (gradeLevelInput?.value) formData.append('grade_level', gradeLevelInput.value);
    if (durationInput?.value) formData.append('duration', durationInput.value);
    if (keywordsInput?.value) formData.append('keywords', keywordsInput.value);

    // Determine content type based on quick-select tags
    let contentType = 'resource'; // default
    const selectedQuickTags = document.querySelectorAll('.quick-tag-btn.selected');
    if (selectedQuickTags.length > 0) {
      contentType = selectedQuickTags[0].dataset.tag;
    }
    formData.append('content_type', contentType);

    // Add smart categorization data if available
    if (this.currentAnalysis) {
      formData.append('auto_categorized', 'true');
      formData.append('categorization_confidence', this.currentAnalysis.overall_confidence.toString());
      formData.append('suggested_tags', JSON.stringify(this.currentAnalysis.suggested_tags || []));
      
      console.log('📊 Including AI analysis data in upload');
    }

    // Upload with progress tracking
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          this.showUploadProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        try {
          const response = JSON.parse(xhr.responseText);
          if (xhr.status === 201 && response.status === 'success') {
            this.showUploadProgress(100);
            resolve(response);
          } else {
            reject(new Error(response.message || 'Upload failed'));
          }
        } catch (error) {
          reject(new Error('Invalid response from server'));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Upload failed'));
      });

      xhr.open('POST', '/api/content/upload');
      xhr.send(formData);
    });
  }

  async assignTagsToContent(contentId, tagIds) {
    try {
      const response = await fetch(`/api/content/${contentId}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tag_ids: tagIds,
          replace: true
        })
      });

      const result = await response.json();
      if (result.status !== 'success') {
        console.warn('Error assigning tags:', result.message);
      }
    } catch (error) {
      console.error('Error assigning tags:', error);
    }
  }

  // Tag Management Functions
  async handleTagInput(query) {
    const suggestions = document.getElementById('tag-suggestions');
    
    if (!query.trim()) {
      suggestions.innerHTML = '';
      return;
    }

    const filteredTags = this.allTags.filter(tag => 
      tag.name.toLowerCase().includes(query.toLowerCase()) &&
      !this.selectedTagIds.has(tag.id)
    );

    let html = '';
    
    // Show existing tags
    filteredTags.forEach(tag => {
      html += `
        <div class="tag-suggestion" onclick="app.selectTag(${tag.id})">
          <span class="tag-chip ${tag.color ? 'colored' : ''}" ${tag.color ? `style="background-color: ${tag.color}"` : ''}>
            ${tag.name}
          </span>
        </div>
      `;
    });

    // Show create new option
    const exactMatch = this.allTags.find(tag => 
      tag.name.toLowerCase() === query.toLowerCase()
    );
    
    if (!exactMatch) {
      html += `
        <div class="tag-suggestion create-new" onclick="app.createAndSelectTag('${query}')">
          Create "${query}"
        </div>
      `;
    }

    suggestions.innerHTML = html;
  }

  selectTag(tagId) {
    this.selectedTagIds.add(tagId);
    this.updateSelectedTags();
    this.updateQuickSelectButtons();
    
    // Clear input and suggestions
    const tagInput = document.getElementById('tag-input');
    const suggestions = document.getElementById('tag-suggestions');
    tagInput.value = '';
    suggestions.innerHTML = '';
  }

  async createAndSelectTag(tagName) {
    try {
      const response = await fetch('/api/tags', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: tagName,
          description: '',
          color: this.getRandomTagColor()
        })
      });

      const result = await response.json();
      
      if (result.status === 'success') {
        // Add to allTags array
        const newTag = {
          id: result.data.id,
          name: tagName,
          color: this.getRandomTagColor()
        };
        this.allTags.push(newTag);
        
        // Select the new tag
        this.selectTag(newTag.id);
        this.showToast('Tag created and added', 'success');
      } else {
        this.showToast('Error creating tag', 'error');
      }
    } catch (error) {
      console.error('Error creating tag:', error);
      this.showToast('Error creating tag', 'error');
    }
  }

  removeTag(tagId) {
    this.selectedTagIds.delete(tagId);
    this.updateSelectedTags();
    this.updateQuickSelectButtons();
  }

  updateSelectedTags() {
    const container = document.getElementById('selected-tags');
    const selectedTags = Array.from(this.selectedTagIds).map(tagId => {
      const tag = this.allTags.find(t => t.id === tagId);
      return tag;
    }).filter(Boolean);

    container.innerHTML = selectedTags.map(tag => `
      <span class="tag-chip ${tag.color ? 'colored' : ''}" ${tag.color ? `style="background-color: ${tag.color}"` : ''}>
        ${tag.name}
        <button type="button" class="tag-chip-remove" onclick="app.removeTag(${tag.id})">&times;</button>
      </span>
    `).join('');
  }

  // Quick-select tag button functionality
  setupQuickSelectButtons() {
    // Add event listeners for quick-select buttons
    const quickButtons = document.querySelectorAll('.quick-tag-btn');
    quickButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        const tagName = button.dataset.tag;
        this.toggleQuickSelectTag(tagName);
      });
    });
  }

  toggleQuickSelectTag(tagName) {
    // Find the tag by name
    const tag = this.allTags.find(t => t.name === tagName);
    if (!tag) {
      console.warn(`Tag not found: ${tagName}`);
      return;
    }

    // Toggle selection
    if (this.selectedTagIds.has(tag.id)) {
      this.selectedTagIds.delete(tag.id);
    } else {
      this.selectedTagIds.add(tag.id);
    }

    this.updateSelectedTags();
    this.updateQuickSelectButtons();
  }

  updateQuickSelectButtons() {
    const quickButtons = document.querySelectorAll('.quick-tag-btn');
    quickButtons.forEach(button => {
      const tagName = button.dataset.tag;
      const tag = this.allTags.find(t => t.name === tagName);
      
      if (tag && this.selectedTagIds.has(tag.id)) {
        button.classList.add('selected');
      } else {
        button.classList.remove('selected');
      }
    });
  }

  getRandomTagColor() {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  // Smart Categorization Integration
  setupSmartCategorizationTriggers() {
    const titleInput = document.getElementById('content-title');
    const descriptionInput = document.getElementById('content-description');
    
    if (titleInput) {
      titleInput.addEventListener('input', () => {
        this.triggerSmartAnalysis();
      });
    }
    
    if (descriptionInput) {
      descriptionInput.addEventListener('input', () => {
        this.triggerSmartAnalysis();
      });
    }
  }

  triggerSmartAnalysis() {
    // Debounce analysis to avoid excessive API calls
    if (this.analysisTimeout) {
      clearTimeout(this.analysisTimeout);
    }
    
    this.analysisTimeout = setTimeout(() => {
      this.performSmartAnalysis();
    }, 1000); // Wait 1 second after last change
  }

  performSmartAnalysis() {
    // Gather current form data
    const titleInput = document.getElementById('content-title');
    const descriptionInput = document.getElementById('content-description');
    
    const metadata = {
      title: titleInput?.value || '',
      description: descriptionInput?.value || '',
      filename: this.currentFile?.name || ''
    };
    
    // Only analyze if we have meaningful content
    if (this.currentFile || (metadata.title && metadata.title.length > 3)) {
      console.log('🚀 Triggering smart analysis...');
      this.smartCategorization.analyzeContent(this.currentFile, metadata);
    }
  }

  // Modal Functions
  showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
    }
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('hidden');
      document.body.style.overflow = '';
    }
  }

  showConfirmDialog(message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const messageEl = document.getElementById('confirm-message');
    const confirmBtn = document.getElementById('confirm-action-btn');
    
    messageEl.textContent = message;
    
    // Remove existing event listeners and add new one
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    newConfirmBtn.addEventListener('click', () => {
      onConfirm();
      this.closeModal('confirm-modal');
    });
    
    this.showModal('confirm-modal');
  }

  // Utility Functions
  showLoading() {
    this.isLoading = true;
    const loading = document.getElementById('loading');
    if (loading) {
      loading.classList.remove('hidden');
    }
  }

  hideLoading() {
    this.isLoading = false;
    const loading = document.getElementById('loading');
    if (loading) {
      loading.classList.add('hidden');
    }
  }

  showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (toast) {
      toast.textContent = message;
      toast.className = `toast ${type}`;
      toast.classList.remove('hidden');
      
      setTimeout(() => {
        toast.classList.add('hidden');
      }, 3000);
    }
  }

  performSearch(query) {
    console.log('Searching for:', query);
    // TODO: Implement search functionality
  }

  refreshCurrentPage() {
    this.loadPageContent(this.currentPage);
  }

  handleAction(action, dataset = {}) {
    switch (action) {
      case 'add-content':
        this.showAddContentDialog();
        break;
      case 'edit-content':
        if (dataset.id) {
          this.editContent(parseInt(dataset.id));
        }
        break;
      case 'delete-content':
        if (dataset.id) {
          this.deleteContent(parseInt(dataset.id));
        }
        break;
      case 'view-content':
        if (dataset.id) {
          this.viewContent(parseInt(dataset.id));
        }
        break;
      case 'import-content':
        this.showToast('Import content functionality coming soon');
        break;
      case 'add-tag':
        this.showToast('Add tag functionality coming soon');
        break;
      case 'add-category':
        this.showToast('Add category functionality coming soon');
        break;
      default:
        console.log('Unknown action:', action);
    }
  }
}

// Smart Categorization Class - Task 1.3
class SmartCategorization {
  constructor(app) {
    this.app = app;
    this.isAnalyzing = false;
    this.currentSuggestions = null;
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Setup event listeners once DOM is ready
    document.addEventListener('DOMContentLoaded', () => {
      const acceptBtn = document.getElementById('accept-suggestions');
      const rejectBtn = document.getElementById('reject-suggestions');

      if (acceptBtn) {
        acceptBtn.addEventListener('click', () => this.acceptAllSuggestions());
      }

      if (rejectBtn) {
        rejectBtn.addEventListener('click', () => this.rejectAllSuggestions());
      }
    });
  }

  async analyzeContent(file, metadata) {
    if (this.isAnalyzing) {
      console.log('Analysis already in progress');
      return;
    }

    this.isAnalyzing = true;
    this.showAnalyzingState();

    try {
      const formData = new FormData();
      
      // Add file if provided
      if (file) {
        formData.append('file', file);
        formData.append('filename', file.name);
      }
      
      // Add metadata
      Object.keys(metadata).forEach(key => {
        if (metadata[key]) {
          formData.append(key, metadata[key]);
        }
      });

      console.log('📊 Calling content analysis API...');
      
      const response = await fetch('/api/content/analyze', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (result.status === 'success' && result.analysis) {
        console.log('✅ Analysis successful:', result.analysis);
        this.currentSuggestions = result.analysis;
        this.displaySuggestions(result.analysis);
        this.app.currentAnalysis = result.analysis;
        
        // Auto-accept high confidence suggestions (>90%)
        if (result.analysis.overall_confidence > 0.9) {
          this.showAutoAcceptedState();
          setTimeout(() => this.acceptAllSuggestions(), 1000);
        } else {
          this.showReadyState();
        }
        
      } else {
        console.warn('Analysis failed:', result.message);
        this.showErrorState(result.message || 'Analysis failed');
      }

    } catch (error) {
      console.error('Content analysis error:', error);
      this.showErrorState('Network error during analysis');
    } finally {
      this.isAnalyzing = false;
    }
  }

  displaySuggestions(analysis) {
    const suggestionsPanel = document.getElementById('smart-suggestions');
    const suggestionGrid = document.getElementById('suggestion-grid');
    
    if (!suggestionsPanel || !suggestionGrid) {
      console.error('Smart suggestions panel not found');
      return;
    }

    // Show the panel
    suggestionsPanel.classList.remove('hidden');

    // Build suggestions HTML
    let suggestionsHTML = '';

    // Content Type suggestion
    if (analysis.content_type) {
      suggestionsHTML += this.buildSuggestionItem(
        'Content Type',
        analysis.content_type,
        analysis.content_type_confidence,
        'content_type'
      );
    }

    // Subject suggestion
    if (analysis.subject) {
      suggestionsHTML += this.buildSuggestionItem(
        'Subject',
        analysis.subject,
        analysis.subject_confidence,
        'subject'
      );
    }

    // Difficulty suggestion
    if (analysis.difficulty) {
      suggestionsHTML += this.buildSuggestionItem(
        'Difficulty',
        analysis.difficulty,
        analysis.difficulty_confidence,
        'difficulty'
      );
    }

    // Grade Level suggestion
    if (analysis.grade_level) {
      suggestionsHTML += this.buildSuggestionItem(
        'Grade Level',
        analysis.grade_level,
        analysis.grade_level_confidence,
        'grade_level'
      );
    }

    // Add suggested tags if available
    if (analysis.suggested_tags && analysis.suggested_tags.length > 0) {
      suggestionsHTML += `
        <div class="suggestion-item" data-type="tags">
          <div class="suggestion-category">Suggested Tags</div>
          <div class="suggested-tags">
            <div class="suggested-tag-chips">
              ${analysis.suggested_tags.map(tag => 
                `<span class="suggested-tag-chip" data-tag="${tag}">${tag}</span>`
              ).join('')}
            </div>
          </div>
        </div>
      `;
    }

    suggestionGrid.innerHTML = suggestionsHTML;

    // Add click handlers for individual suggestions
    this.setupSuggestionClickHandlers();
  }

  buildSuggestionItem(category, value, confidence, type) {
    const confidenceLevel = confidence > 0.8 ? 'high' : confidence > 0.6 ? 'medium' : 'low';
    const confidencePercent = Math.round(confidence * 100);
    
    return `
      <div class="suggestion-item ${confidence > 0.9 ? 'auto-accepted' : ''}" data-type="${type}" data-value="${value}" data-confidence="${confidence}">
        <div class="suggestion-category">${category}</div>
        <div class="suggestion-value">${this.formatSuggestionValue(value)}</div>
        <div class="suggestion-confidence">
          <div class="confidence-bar">
            <div class="confidence-fill ${confidenceLevel}" style="width: ${confidencePercent}%"></div>
          </div>
          <span class="confidence-badge ${confidenceLevel}">${confidencePercent}%</span>
        </div>
      </div>
    `;
  }

  formatSuggestionValue(value) {
    // Convert technical values to user-friendly display
    const mappings = {
      'lesson-plan': '📝 Lesson Plan',
      'worksheet': '📄 Worksheet', 
      'assessment': '✅ Assessment',
      'resource': '📚 Resource',
      'activity': '🎯 Activity',
      'English': '📖 English',
      'Mathematics': '🔢 Mathematics',
      'Science': '🔬 Science',
      'Religious-Education': '✝️ Religious Education',
      'Learning-Support': '🤝 Learning Support',
      'beginner': '🟢 Beginner',
      'intermediate': '🟡 Intermediate',
      'advanced': '🔴 Advanced',
      'early-years': '👶 Early Years',
      'primary': '🎒 Primary',
      'secondary': '🎓 Secondary',
      'adult-ed': '👨‍🎓 Adult Education'
    };
    
    return mappings[value] || value;
  }

  setupSuggestionClickHandlers() {
    // Individual suggestion item clicks
    document.querySelectorAll('.suggestion-item').forEach(item => {
      item.addEventListener('click', () => {
        item.classList.toggle('selected');
      });
    });

    // Individual tag clicks
    document.querySelectorAll('.suggested-tag-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        e.stopPropagation();
        chip.classList.toggle('accepted');
      });
    });
  }

  acceptAllSuggestions() {
    if (!this.currentSuggestions) return;

    console.log('✅ Accepting all suggestions');
    
    // Apply content type suggestion
    if (this.currentSuggestions.content_type) {
      this.applyContentTypeSuggestion(this.currentSuggestions.content_type);
    }

    // Apply subject suggestion
    if (this.currentSuggestions.subject) {
      this.applySubjectSuggestion(this.currentSuggestions.subject);
    }

    // Apply suggested tags
    if (this.currentSuggestions.suggested_tags) {
      this.applySuggestedTags(this.currentSuggestions.suggested_tags);
    }

    // Update visual state
    document.querySelectorAll('.suggestion-item').forEach(item => {
      item.classList.add('selected');
    });

    document.querySelectorAll('.suggested-tag-chip').forEach(chip => {
      chip.classList.add('accepted');
    });

    this.app.showToast('✨ AI suggestions applied successfully!', 'success');
    this.hideSuggestionsPanel();
  }

  rejectAllSuggestions() {
    console.log('❌ Rejecting all suggestions');
    this.currentSuggestions = null;
    this.app.currentAnalysis = null;
    this.hideSuggestionsPanel();
    this.app.showToast('Suggestions rejected', 'info');
  }

  applyContentTypeSuggestion(contentType) {
    // Find and select the corresponding quick-select button
    const quickButton = document.querySelector(`[data-tag="${contentType}"]`);
    if (quickButton && !quickButton.classList.contains('selected')) {
      quickButton.click();
    }
  }

  applySubjectSuggestion(subject) {
    // Set the subject dropdown
    const subjectSelect = document.getElementById('content-subject');
    if (subjectSelect) {
      subjectSelect.value = subject;
    }
  }

  applySuggestedTags(tags) {
    // Add suggested tags to selected tags
    tags.forEach(async (tagName) => {
      // Find existing tag or create new one
      let existingTag = this.app.allTags.find(t => 
        t.name.toLowerCase() === tagName.toLowerCase()
      );

      if (existingTag) {
        this.app.selectedTagIds.add(existingTag.id);
      } else {
        // Create new tag
        try {
          await this.app.createAndSelectTag(tagName);
        } catch (error) {
          console.warn(`Failed to create tag: ${tagName}`, error);
        }
      }
    });

    // Update UI
    this.app.updateSelectedTags();
    this.app.updateQuickSelectButtons();
  }

  showAnalyzingState() {
    const statusElement = document.getElementById('smart-suggestions-status');
    const suggestionsPanel = document.getElementById('smart-suggestions');
    
    if (statusElement) {
      statusElement.textContent = 'Analyzing content...';
      statusElement.className = 'smart-suggestions-status analyzing';
    }
    
    if (suggestionsPanel) {
      suggestionsPanel.classList.remove('hidden');
      const suggestionGrid = document.getElementById('suggestion-grid');
      if (suggestionGrid) {
        suggestionGrid.innerHTML = `
          <div class="analyzing-indicator">
            <div class="analyzing-spinner"></div>
            <span>AI is analyzing your content...</span>
          </div>
        `;
      }
    }
  }

  showReadyState() {
    const statusElement = document.getElementById('smart-suggestions-status');
    if (statusElement) {
      statusElement.textContent = 'Ready for review';
      statusElement.className = 'smart-suggestions-status ready';
    }
  }

  showAutoAcceptedState() {
    const statusElement = document.getElementById('smart-suggestions-status');
    if (statusElement) {
      statusElement.textContent = 'High confidence - auto-applying';
      statusElement.className = 'smart-suggestions-status ready';
    }
  }

  showErrorState(message) {
    const statusElement = document.getElementById('smart-suggestions-status');
    const suggestionGrid = document.getElementById('suggestion-grid');
    
    if (statusElement) {
      statusElement.textContent = 'Analysis failed';
      statusElement.className = 'smart-suggestions-status error';
    }
    
    if (suggestionGrid) {
      suggestionGrid.innerHTML = `
        <div class="error-message">
          <span>⚠️ ${message}</span>
          <small>Using manual categorization instead.</small>
        </div>
      `;
    }
  }

  hideSuggestionsPanel() {
    const suggestionsPanel = document.getElementById('smart-suggestions');
    if (suggestionsPanel) {
      setTimeout(() => {
        suggestionsPanel.classList.add('hidden');
      }, 2000); // Hide after 2 seconds
    }
  }

  // Enhanced upload flow integration
  async enhancedFileSelect(file, metadata) {
    console.log('🧠 Enhanced file selection with smart categorization');
    
    // Only analyze if we have substantial content
    if (file || (metadata.title && metadata.title.length > 3)) {
      await this.analyzeContent(file, metadata);
    }
  }
}

// Task 2.2: Auto-Upload Handler - Zero-Touch Content Processing
class AutoUploadHandler {
  constructor(app) {
    this.app = app;
    this.dropZone = null;
    this.isProcessing = false;
    this.processedFiles = new Set();
    this.setupDropZone();
  }

  setupDropZone() {
    // Create auto-upload drop zone if not exists
    this.createAutoUploadUI();
    
    // Setup drag and drop events
    this.dropZone = document.getElementById('auto-upload-zone');
    if (!this.dropZone) return;

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      this.dropZone.addEventListener(eventName, this.preventDefaults, false);
      document.body.addEventListener(eventName, this.preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
      this.dropZone.addEventListener(eventName, () => this.highlight(), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      this.dropZone.addEventListener(eventName, () => this.unhighlight(), false);
    });

    // Handle dropped files
    this.dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);

    // Also handle click to select files
    this.dropZone.addEventListener('click', () => this.handleClick(), false);
  }

  createAutoUploadUI() {
    // Check if auto-upload section exists
    const existingZone = document.getElementById('auto-upload-zone');
    if (existingZone) return;

    // Create auto-upload section in the content page
    const contentPage = document.querySelector('.page-content');
    if (!contentPage) return;

    const autoUploadHTML = `
      <div class="auto-upload-section" id="auto-upload-section">
        <h3>🚀 Zero-Touch Auto-Upload</h3>
        <p class="auto-upload-description">
          Drop files here for automatic AI-powered categorization and upload.
          No manual data entry required!
        </p>
        <div id="auto-upload-zone" class="auto-upload-zone">
          <div class="upload-icon">📁</div>
          <h4>Drop files here</h4>
          <p>or click to select files</p>
          <p class="supported-types">Supports: PDF, Word, PowerPoint, Text files</p>
        </div>
        <div id="auto-upload-results" class="auto-upload-results hidden">
          <h4>Processing Results</h4>
          <div id="upload-results-list"></div>
        </div>
      </div>
    `;

    // Add to the beginning of content page if viewing content
    if (this.app.currentPage === 'content') {
      const contentGrid = document.querySelector('.content-grid');
      if (contentGrid) {
        contentGrid.insertAdjacentHTML('beforebegin', autoUploadHTML);
      }
    }
  }

  preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  highlight() {
    this.dropZone.classList.add('highlight');
  }

  unhighlight() {
    this.dropZone.classList.remove('highlight');
  }

  async handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    await this.handleFiles(files);
  }

  handleClick() {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.multiple = true;
    fileInput.accept = '.pdf,.doc,.docx,.txt,.rtf,.odt,.ppt,.pptx';
    
    fileInput.addEventListener('change', async (e) => {
      const files = e.target.files;
      await this.handleFiles(files);
    });
    
    fileInput.click();
  }

  async handleFiles(files) {
    if (this.isProcessing) {
      this.app.showToast('Please wait for current upload to complete', 'warning');
      return;
    }

    const fileArray = [...files];
    
    // Filter valid files
    const validFiles = fileArray.filter(file => this.isValidFile(file));
    
    if (validFiles.length === 0) {
      this.app.showToast('No valid files selected', 'error');
      return;
    }

    // Show results section
    document.getElementById('auto-upload-results').classList.remove('hidden');
    
    // Process files
    for (const file of validFiles) {
      await this.autoUploadFile(file);
    }
  }

  isValidFile(file) {
    const allowedExtensions = [
      '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
      '.ppt', '.pptx', '.odp'
    ];
    
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    return allowedExtensions.includes(ext);
  }

  async autoUploadFile(file) {
    // Prevent duplicate uploads
    const fileId = `${file.name}-${file.size}-${file.lastModified}`;
    if (this.processedFiles.has(fileId)) {
      return;
    }
    
    this.processedFiles.add(fileId);
    
    // Create progress indicator
    const resultItem = this.createResultItem(file);
    const resultsList = document.getElementById('upload-results-list');
    resultsList.appendChild(resultItem);
    
    try {
      // Show processing state
      this.updateResultItem(resultItem, 'processing', 'Analyzing content with AI...');
      
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Call auto-upload endpoint
      const response = await fetch('/api/content/auto-upload', {
        method: 'POST',
        body: formData
      });
      
      console.log('Auto-upload response status:', response.status);
      const responseText = await response.text();
      console.log('Auto-upload response text:', responseText);
      
      let result;
      try {
        result = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Failed to parse response as JSON:', parseError);
        throw new Error('Invalid server response');
      }
      
      if (response.ok && result.status === 'success') {
        // Show success with generated metadata
        this.updateResultItem(resultItem, 'success', 
          `✅ Auto-saved as: "${result.data.title}"`, result.data);
        
        // Refresh content grid after successful upload
        setTimeout(() => {
          this.app.refreshCurrentPage();
        }, 1000);
      } else {
        throw new Error(result.message || 'Auto-upload failed');
      }
      
    } catch (error) {
      console.error('Auto-upload error:', error);
      this.updateResultItem(resultItem, 'error', 
        `❌ Failed: ${error.message}`);
    }
  }

  createResultItem(file) {
    const item = document.createElement('div');
    item.className = 'upload-result-item';
    item.innerHTML = `
      <div class="result-file-info">
        <span class="file-icon">${this.app.getFileIcon(file.name)}</span>
        <span class="file-name">${file.name}</span>
        <span class="file-size">(${this.app.formatFileSize(file.size)})</span>
      </div>
      <div class="result-status">
        <div class="status-spinner"></div>
        <span class="status-text">Preparing...</span>
      </div>
      <div class="result-metadata hidden"></div>
    `;
    return item;
  }

  updateResultItem(item, status, message, metadata = null) {
    const statusDiv = item.querySelector('.result-status');
    const statusText = item.querySelector('.status-text');
    
    // Remove spinner if not processing
    if (status !== 'processing') {
      const spinner = statusDiv.querySelector('.status-spinner');
      if (spinner) spinner.remove();
    }
    
    // Update status
    statusDiv.className = `result-status ${status}`;
    statusText.textContent = message;
    
    // Show metadata if successful
    if (status === 'success' && metadata) {
      const metadataDiv = item.querySelector('.result-metadata');
      metadataDiv.innerHTML = `
        <div class="metadata-grid">
          <div class="metadata-item">
            <strong>Subject:</strong> ${metadata.subject}
          </div>
          <div class="metadata-item">
            <strong>Type:</strong> ${metadata.content_type}
          </div>
          <div class="metadata-item">
            <strong>Grade:</strong> ${metadata.grade_level}
          </div>
          <div class="metadata-item">
            <strong>Difficulty:</strong> ${metadata.difficulty_level}
          </div>
          <div class="metadata-item">
            <strong>Duration:</strong> ${metadata.duration} min
          </div>
          <div class="metadata-item">
            <strong>Tags:</strong> ${metadata.tags.join(', ') || 'None'}
          </div>
        </div>
        <div class="metadata-description">
          <strong>Description:</strong> ${metadata.description}
        </div>
      `;
      metadataDiv.classList.remove('hidden');
    }
  }
}

// Initialize the app
const app = new App();

// Start the app when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => app.init());
} else {
  app.init();
}

// Export for global access
window.app = app; 