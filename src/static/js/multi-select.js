class MultiSelect {
    constructor(container, choices) {
        this.container = container;
        this.choices = choices;
        this.selectedItems = new Set();
        this.input = container.querySelector('.multi-select-input');
        this.tagsContainer = container.querySelector('.multi-select-tags');
        this.dropdown = container.querySelector('.multi-select-dropdown');
        this.hiddenField = container.querySelector('select[multiple]');
        
        this.init();
    }
    
    init() {
        // Initialize with existing values from the hidden field
        const existingValues = Array.from(this.hiddenField.selectedOptions).map(option => option.value);
        existingValues.forEach(value => {
            const choice = this.choices.find(c => c.value === value);
            if (choice) {
                this.selectedItems.add(choice);
                this.addTag(choice);
            }
        });
        
        // Event listeners
        this.input.addEventListener('input', (e) => this.handleInput(e));
        this.input.addEventListener('focus', () => this.showDropdown());
        this.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    handleInput(e) {
        const query = e.target.value.toLowerCase();
        this.showDropdown(query);
    }
    
    handleKeydown(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const activeOption = this.dropdown.querySelector('.multi-select-option.active');
            if (activeOption) {
                this.selectChoice(parseInt(activeOption.dataset.value));
            }
        } else if (e.key === 'Escape') {
            this.hideDropdown();
        } else if (e.key === 'Backspace' && this.input.value === '' && this.selectedItems.size > 0) {
            // Remove last selected item
            const lastItem = Array.from(this.selectedItems).pop();
            this.removeChoice(lastItem.value);
        }
    }
    
    showDropdown(query = '') {
        this.dropdown.innerHTML = '';
        
        const filteredChoices = this.choices.filter(choice => {
            if (this.selectedItems.has(choice)) return false;
            return choice.label.toLowerCase().includes(query);
        });
        
        if (filteredChoices.length === 0) {
            this.dropdown.innerHTML = '<div class="multi-select-no-results">No results found</div>';
        } else {
            filteredChoices.forEach((choice, index) => {
                const option = document.createElement('div');
                option.className = 'multi-select-option';
                option.dataset.value = choice.value;
                option.textContent = choice.label;
                option.addEventListener('click', () => this.selectChoice(choice.value));
                option.addEventListener('mouseenter', () => {
                    this.dropdown.querySelectorAll('.multi-select-option').forEach(opt => opt.classList.remove('active'));
                    option.classList.add('active');
                });
                this.dropdown.appendChild(option);
            });
        }
        
        this.dropdown.style.display = 'block';
    }
    
    hideDropdown() {
        this.dropdown.style.display = 'none';
    }
    
    selectChoice(value) {
        const choice = this.choices.find(c => c.value == value);
        if (choice && !this.selectedItems.has(choice)) {
            this.selectedItems.add(choice);
            this.addTag(choice);
            this.updateHiddenField();
            this.input.value = '';
            this.hideDropdown();
        }
    }
    
    removeChoice(value) {
        const choice = this.choices.find(c => c.value == value);
        if (choice) {
            this.selectedItems.delete(choice);
            this.removeTag(value);
            this.updateHiddenField();
        }
    }
    
    addTag(choice) {
        const tag = document.createElement('div');
        tag.className = 'multi-select-tag';
        tag.dataset.value = choice.value;
        tag.innerHTML = `
            <span class="multi-select-tag-text">${choice.label}</span>
            <button type="button" class="multi-select-tag-remove">×</button>
        `;
        
        tag.querySelector('.multi-select-tag-remove').addEventListener('click', () => {
            this.removeChoice(choice.value);
        });
        
        this.tagsContainer.appendChild(tag);
    }
    
    removeTag(value) {
        const tag = this.tagsContainer.querySelector(`[data-value="${value}"]`);
        if (tag) {
            tag.remove();
        }
    }
    
    updateHiddenField() {
        this.hiddenField.innerHTML = '';
        this.selectedItems.forEach(choice => {
            const option = document.createElement('option');
            option.value = choice.value;
            option.selected = true;
            option.textContent = choice.label;
            this.hiddenField.appendChild(option);
        });
    }
}

// Initialize multi-select components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    const containers = document.querySelectorAll('.multi-select-container');
    
    containers.forEach(container => {
        const fieldName = container.dataset.field;
        const hiddenField = container.querySelector('select[multiple]');
        
        // Extract choices from the hidden field options
        const choices = Array.from(hiddenField.options).map(option => ({
            value: option.value,
            label: option.textContent
        }));
        
        const instance = new MultiSelect(container, choices);
        container.multiSelectInstance = instance;
    });
});