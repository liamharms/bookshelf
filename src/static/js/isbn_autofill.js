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
            // Select the existing author
            if (authorsSelect.tomselect) {
                authorsSelect.tomselect.addItem(exactMatch.id);
            } else {
                const option = Array.from(authorsSelect.options).find(o => o.value === exactMatch.id);
                if (option) option.selected = true;
            }
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
            // Select the existing tag
            if (tagsSelect.tomselect) {
                tagsSelect.tomselect.addItem(exactMatch.id);
            } else {
                const option = Array.from(tagsSelect.options).find(o => o.value === exactMatch.id);
                if (option) option.selected = true;
            }
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
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="batchMatchModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Match or Add Authors and Tags</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        ${unmatchedAuthors.length > 0 ? `
                            <h6 class="mb-3">Authors</h6>
                            ${unmatchedAuthors.map((author, idx) => createMatchRow('author', author, idx)).join('')}
                            <hr class="my-4">
                        ` : ''}
                        
                        ${unmatchedTags.length > 0 ? `
                            <h6 class="mb-3">Tags</h6>
                            ${unmatchedTags.map((tag, idx) => createMatchRow('tag', tag, idx)).join('')}
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="processBatchSelections()">Apply Selections</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove old modal if exists
    const oldModal = document.getElementById('batchMatchModal');
    if (oldModal) oldModal.remove();
    
    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('batchMatchModal'));
    modal.show();
}

function createMatchRow(type, item, index) {
    const name = type === 'author' ? item.name : item.label;
    const hasSimilar = item.similar && item.similar.length > 0;
    
    return `
        <div class="card mb-3" data-type="${type}" data-index="${index}">
            <div class="card-body">
                <div class="mb-2">
                    <strong>${name}</strong>
                    <span class="badge bg-secondary ms-2">From ISBN data</span>
                </div>
                
                ${hasSimilar ? `
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="radio" name="${type}_${index}" id="${type}_${index}_similar" value="similar" checked>
                        <label class="form-check-label" for="${type}_${index}_similar">
                            Use similar existing ${type}
                        </label>
                    </div>
                    <select class="form-select form-select-sm ms-4 mb-2" id="${type}_${index}_select">
                        ${item.similar.map(s => `
                            <option value="${s.id}">
                                ${type === 'author' ? s.name : s.label} 
                                <span class="text-muted">(${s.score}% match)</span>
                            </option>
                        `).join('')}
                    </select>
                ` : ''}
                
                <div class="form-check mb-2">
                    <input class="form-check-input" type="radio" name="${type}_${index}" id="${type}_${index}_new" value="new" ${!hasSimilar ? 'checked' : ''}>
                    <label class="form-check-label" for="${type}_${index}_new">
                        Add as new ${type}
                    </label>
                </div>
                
                <div class="form-check">
                    <input class="form-check-input" type="radio" name="${type}_${index}" id="${type}_${index}_ignore" value="ignore">
                    <label class="form-check-label" for="${type}_${index}_ignore">
                        Ignore (don't add)
                    </label>
                </div>
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
            
            // Add to form
            if (authorsSelect.tomselect) {
                authorsSelect.tomselect.addItem(authorId);
            } else {
                const option = Array.from(authorsSelect.options).find(o => o.value === authorId);
                if (option) option.selected = true;
            }
        } else {
            // Create new author
            const newAuthor = await createAuthor(unmatchedAuthors[i].name);
            if (newAuthor) {
                // Add to form options and select it
                if (authorsSelect.tomselect) {
                    authorsSelect.tomselect.addOption({value: newAuthor.id, text: newAuthor.name});
                    authorsSelect.tomselect.addItem(newAuthor.id);
                } else {
                    const option = new Option(newAuthor.name, newAuthor.id, true, true);
                    authorsSelect.add(option);
                }
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
            
            // Add to form
            if (tagsSelect.tomselect) {
                tagsSelect.tomselect.addItem(tagId);
            } else {
                const option = Array.from(tagsSelect.options).find(o => o.value === tagId);
                if (option) option.selected = true;
            }
        } else {
            // Create new tag
            const newTag = await createTag(unmatchedTags[i].label);
            if (newTag) {
                // Add to form options and select it
                if (tagsSelect.tomselect) {
                    tagsSelect.tomselect.addOption({value: newTag.id, text: newTag.label});
                    tagsSelect.tomselect.addItem(newTag.id);
                } else {
                    const option = new Option(newTag.label, newTag.id, true, true);
                    tagsSelect.add(option);
                }
            }
        }
    }
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('batchMatchModal'));
    modal.hide();
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