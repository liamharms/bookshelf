document.addEventListener('DOMContentLoaded', function() {
    // Initialize Tom Select for all select fields
    const selects = document.querySelectorAll('.tom-select');
    let tomSelectInstances = {};
    
    selects.forEach(function(select) {
        tomSelectInstances[select.id] = new TomSelect(select, {
            plugins: ['remove_button', 'clear_button'],
            create: false,
            sortField: {
                field: "text",
                direction: "asc"
            },
            searchField: ['text'],
            placeholder: select.getAttribute('placeholder') || 'Search and select...',
            maxOptions: null,
            closeAfterSelect: !select.hasAttribute('multiple')
        });
    });
});