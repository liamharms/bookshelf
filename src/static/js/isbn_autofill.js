// Store unmatched items for batch processing
let unmatchedAuthors = [];
let unmatchedTags = [];

async function lookupISBN() {
    const isbnInput = document.querySelector('input[name="isbn"]');
    const isbn = isbnInput.value.trim().replace(/[-\s]/g, '');
    
    if (!isbn || isbn.length < 10) {
        return;
    }
    
    try {
        isbnInput.disabled = true;
        
        const response = await fetch(`/api/isbn-lookup/${isbn}`);
        const data = await response.json();
        
        if (data.success) {
            // Fill simple fields
            fillSimpleFields(data);
            
            // Reset unmatched items
            unmatchedAuthors = [];
            unmatchedTags = [];
            
            // Process authors
            if (data.authors && data.authors.length > 0) {
                await processAuthors(data.authors);
            }
            
            // Process tags/categories
            if (data.categories && data.categories.length > 0) {
                await processTags(data.categories);
            }
            
            // Show batch modal if there are unmatched items
            if (unmatchedAuthors.length > 0 || unmatchedTags.length > 0) {
                showBatchMatchModal();
            }
            
            isbnInput.classList.add('is-valid');
            setTimeout(() => isbnInput.classList.remove('is-valid'), 2000);
            
        } else {
            isbnInput.classList.add('is-invalid');
            setTimeout(() => isbnInput.classList.remove('is-invalid'), 2000);
            console.error('ISBN lookup failed:', data.error);
        }
        
    } catch (error) {
        console.error('Error looking up ISBN:', error);
        isbnInput.classList.add('is-invalid');
        setTimeout(() => isbnInput.classList.remove('is-invalid'), 2000);
    } finally {
        isbnInput.disabled = false;
    }
}

function fillSimpleFields(data) {
    // Fill title
    const titleInput = document.querySelector('input[name="title"]');
    if (titleInput && data.title) {
        titleInput.value = data.title;
    }
    
    // Fill description
    const descriptionInput = document.querySelector('textarea[name="description"]');
    if (descriptionInput && data.description) {
        descriptionInput.value = data.description;
    }
    
    // Fill cover URL
    const coverInput = document.querySelector('input[name="cover_url"]');
    if (coverInput && data.cover_url) {
        coverInput.value = data.cover_url;
    }
}

async function processAuthors(authorNames) {
    const authorsSelect = document.querySelector('select[name="authors"]');
    if (!authorsSelect) return;
    
    // Get existing options
    const existingAuthors = Array.from(authorsSelect.options).map(opt => ({
        id: opt.value,
        name: opt.text.toLowerCase()
    }));
    
    for (const authorName of authorNames) {
        // Check for exact match (case-insensitive)
        const exactMatch = existingAuthors.find(a => 
            a.name === authorName.toLowerCase()
        );
        
        if (exactMatch) {
            // Select the existing author using our new multi-select
            selectMultiChoice('authors', exactMatch.id);
        } else {
            // Search for similar authors
            const similarAuthors = await searchSimilarAuthors(authorName);
            unmatchedAuthors.push({
                name: authorName,
                similar: similarAuthors
            });
        }
    }
}

async function processTags(tagLabels) {
    const tagsSelect = document.querySelector('select[name="tags"]');
    if (!tagsSelect) return;
    
    // Get existing options
    const existingTags = Array.from(tagsSelect.options).map(opt => ({
        id: opt.value,
        label: opt.text.toLowerCase()
    }));
    
    for (const tagLabel of tagLabels) {
        // Check for exact match (case-insensitive)
        const exactMatch = existingTags.find(t => 
            t.label === tagLabel.toLowerCase()
        );
        
        if (exactMatch) {
            // Select the existing tag using our new multi-select
            selectMultiChoice('tags', exactMatch.id);
        } else {
            // Search for similar tags
            const similarTags = await searchSimilarTags(tagLabel);
            unmatchedTags.push({
                label: tagLabel,
                similar: similarTags
            });
        }
    }
}

async function searchSimilarAuthors(name) {
    try {
        const response = await fetch('/api/authors/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();
        return data.success ? data.matches : [];
    } catch (error) {
        console.error('Error searching authors:', error);
        return [];
    }
}

async function searchSimilarTags(label) {
    try {
        const response = await fetch('/api/tags/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ label })
        });
        const data = await response.json();
        return data.success ? data.matches : [];
    } catch (error) {
        console.error('Error searching tags:', error);
        return [];
    }
}

function showBatchMatchModal() {
    // Create modal HTML using the application's modal structure
    const modalHtml = `
        <div id="batchMatchModal" class="modal">
            <div class="modal-overlay" onclick="closeBatchMatchModal()"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h3 class="modal-title">Match or Add Authors and Tags</h3>
                    <button class="modal-close" onclick="closeBatchMatchModal()">&times;</button>
                </div>
                <div class="modal-body">
                    ${unmatchedAuthors.length > 0 ? `
                        <h6 style="margin-bottom: 1rem; font-weight: bold;">Authors</h6>
                        ${unmatchedAuthors.map((author, idx) => createMatchRow('author', author, idx)).join('')}
                        <hr style="margin: 1.5rem 0; border: none; border-top: 1px solid var(--border-color);">
                    ` : ''}
                    
                    ${unmatchedTags.length > 0 ? `
                        <h6 style="margin-bottom: 1rem; font-weight: bold;">Tags</h6>
                        ${unmatchedTags.map((tag, idx) => createMatchRow('tag', tag, idx)).join('')}
                    ` : ''}
                </div>
                <div class="modal-footer">
                    <button type="button" class="button button-secondary" onclick="closeBatchMatchModal()">Cancel</button>
                    <button type="button" class="button button-primary" onclick="processBatchSelections()">Apply Selections</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove old modal if exists
    const oldModal = document.getElementById('batchMatchModal');
    if (oldModal) oldModal.remove();
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal using the application's method
    document.getElementById('batchMatchModal').classList.add('active');
}

function closeBatchMatchModal() {
    const modal = document.getElementById('batchMatchModal');
    if (modal) {
        modal.classList.remove('active');
        // Remove modal from DOM after closing
        setTimeout(() => modal.remove(), 300);
    }
}

function createMatchRow(type, item, index) {
    const name = type === 'author' ? item.name : item.label;
    const hasSimilar = item.similar && item.similar.length > 0;
    
    return `
        <div style="border: 1px solid var(--border-color); padding: 1rem; margin-bottom: 1rem; background-color: var(--bg-primary);" data-type="${type}" data-index="${index}">
            <div style="margin-bottom: 0.5rem;">
                <strong>${name}</strong>
                <span style="background-color: var(--bg-secondary); color: var(--text-secondary); padding: 0.25rem 0.5rem; margin-left: 0.5rem; font-size: 0.8rem;">From ISBN data</span>
            </div>
            
            ${hasSimilar ? `
                <div style="margin-bottom: 0.5rem;">
                    <label style="display: flex; align-items: center; margin-bottom: 0.5rem; cursor: pointer;">
                        <input type="radio" name="${type}_${index}" value="similar" checked style="margin-right: 0.5rem;">
                        Use similar existing ${type}
                    </label>
                    <select id="${type}_${index}_select" style="margin-left: 1.5rem; margin-bottom: 0.5rem; width: 100%; max-width: 300px; padding: 0.5rem; background-color: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-primary);">
                        ${item.similar.map(s => `
                            <option value="${s.id}">
                                ${type === 'author' ? s.name : s.label} (${s.score}% match)
                            </option>
                        `).join('')}
                    </select>
                </div>
            ` : ''}
            
            <div style="margin-bottom: 0.5rem;">
                <label style="display: flex; align-items: center; margin-bottom: 0.5rem; cursor: pointer;">
                    <input type="radio" name="${type}_${index}" value="new" ${!hasSimilar ? 'checked' : ''} style="margin-right: 0.5rem;">
                    Add as new ${type}
                </label>
            </div>
            
            <div style="margin-bottom: 0;">
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="radio" name="${type}_${index}" value="ignore" style="margin-right: 0.5rem;">
                    Ignore (don't add)
                </label>
            </div>
        </div>
    `;
}

async function processBatchSelections() {
    const authorsSelect = document.querySelector('select[name="authors"]');
    const tagsSelect = document.querySelector('select[name="tags"]');
    
    // Process authors
    for (let i = 0; i < unmatchedAuthors.length; i++) {
        const card = document.querySelector(`[data-type="author"][data-index="${i}"]`);
        const choice = card.querySelector(`input[name="author_${i}"]:checked`).value;
        
        if (choice === 'ignore') {
            // Skip this author
            continue;
        } else if (choice === 'similar') {
            const selectEl = card.querySelector(`#author_${i}_select`);
            const authorId = selectEl.value;
            
            // Add to form using our new multi-select
            selectMultiChoice('authors', authorId);
        } else {
            // Create new author
            const newAuthor = await createAuthor(unmatchedAuthors[i].name);
            if (newAuthor) {
                // Add to form options and select it using our new multi-select
                addMultiSelectOption('authors', newAuthor.id, newAuthor.name);
                selectMultiChoice('authors', newAuthor.id);
            }
        }
    }
    
    // Process tags
    for (let i = 0; i < unmatchedTags.length; i++) {
        const card = document.querySelector(`[data-type="tag"][data-index="${i}"]`);
        const choice = card.querySelector(`input[name="tag_${i}"]:checked`).value;
        
        if (choice === 'ignore') {
            // Skip this tag
            continue;
        } else if (choice === 'similar') {
            const selectEl = card.querySelector(`#tag_${i}_select`);
            const tagId = selectEl.value;
            
            // Add to form using our new multi-select
            selectMultiChoice('tags', tagId);
        } else {
            // Create new tag
            const newTag = await createTag(unmatchedTags[i].label);
            if (newTag) {
                // Add to form options and select it using our new multi-select
                addMultiSelectOption('tags', newTag.id, newTag.label);
                selectMultiChoice('tags', newTag.id);
            }
        }
    }
    
    // Close modal using the application's method
    closeBatchMatchModal();
}

async function createAuthor(name) {
    try {
        const response = await fetch('/api/authors/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await response.json();
        return data.success ? data.author : null;
    } catch (error) {
        console.error('Error creating author:', error);
        return null;
    }
}

async function createTag(label) {
    try {
        const response = await fetch('/api/tags/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ label, type: 'genre' })
        });
        const data = await response.json();
        return data.success ? data.tag : null;
    } catch (error) {
        console.error('Error creating tag:', error);
        return null;
    }
}

// Helper functions to interact with our new multi-select components
function selectMultiChoice(fieldName, value) {
    const container = document.querySelector(`[data-field="${fieldName}"]`);
    if (!container) return;
    
    const input = container.querySelector('.multi-select-input');
    const choice = {
        value: value.toString(),
        label: getChoiceLabel(fieldName, value)
    };
    
    // Trigger the selection through the MultiSelect instance
    const multiSelectInstance = container.multiSelectInstance;
    if (multiSelectInstance) {
        multiSelectInstance.selectChoice(value);
    }
}

function addMultiSelectOption(fieldName, value, label) {
    const container = document.querySelector(`[data-field="${fieldName}"]`);
    if (!container) return;
    
    // Add option to hidden select field
    const hiddenSelect = container.querySelector('select[multiple]');
    if (hiddenSelect) {
        const option = new Option(label, value.toString(), false, false);
        hiddenSelect.add(option);
    }
    
    // Update choices array in MultiSelect instance
    const multiSelectInstance = container.multiSelectInstance;
    if (multiSelectInstance) {
        multiSelectInstance.choices.push({
            value: value.toString(),
            label: label
        });
    }
}

function getChoiceLabel(fieldName, value) {
    const container = document.querySelector(`[data-field="${fieldName}"]`);
    if (!container) return value;
    
    const hiddenSelect = container.querySelector('select[multiple]');
    if (hiddenSelect) {
        const option = Array.from(hiddenSelect.options).find(o => o.value === value.toString());
        return option ? option.textContent : value;
    }
    
    return value;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    const isbnInput = document.querySelector('input[name="isbn"]');
    
    if (isbnInput) {
        isbnInput.addEventListener('blur', lookupISBN);
        
        isbnInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                lookupISBN();
            }
        });
    }
});