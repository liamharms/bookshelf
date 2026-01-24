// Reusable tree view functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle tree toggle buttons
    document.querySelectorAll('[data-tree-toggle]').forEach(function(toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const itemId = this.getAttribute('data-tree-toggle');
            const childrenContainer = document.querySelector(`[data-tree-children="${itemId}"]`);
            
            if (childrenContainer) {
                childrenContainer.classList.toggle('collapsed');
                
                // Update arrow direction
                if (childrenContainer.classList.contains('collapsed')) {
                    this.textContent = '▶';
                } else {
                    this.textContent = '▼';
                }
            }
        });
    });

    // Optional: Expand/collapse all functionality
    window.expandAllTree = function() {
        document.querySelectorAll('.tree-children').forEach(function(children) {
            children.classList.remove('collapsed');
        });
        document.querySelectorAll('[data-tree-toggle]').forEach(function(btn) {
            if (btn.textContent.trim()) {
                btn.textContent = '▼';
            }
        });
    };

    window.collapseAllTree = function() {
        document.querySelectorAll('.tree-children').forEach(function(children) {
            children.classList.add('collapsed');
        });
        document.querySelectorAll('[data-tree-toggle]').forEach(function(btn) {
            if (btn.textContent.trim()) {
                btn.textContent = '▶';
            }
        });
    };
});