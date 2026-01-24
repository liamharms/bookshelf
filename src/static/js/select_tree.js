function toggleLocationNode_{field_id}(button) {{

    const item = button.closest('.location-tree-item');
    const children = item.querySelector('.location-children')

    if (children) {{
        children.classList.toggle('collapsed');
        button.textContent = children.classList.contains('collapsed') ? '▶' : '▼';
    }}

}}



function selectLocation_{field_id}(value) {{

    document.getElementById('{field_id}').value = value;

}}



function filterLocations_{field_id}(searchTerm) {{

    const items = document.querySelectorAll('#{field_id}_tree .location-tree-item');

    const term = searchTerm.toLowerCase();

    

    items.forEach(item => {{

        const locationName = item.getAttribute('data-location-name').toLowerCase();

        const matches = locationName.includes(term);

        

        if (term === '' || matches) {{

            item.classList.remove('hidden');

            

            // If item matches, expand all parent nodes

            if (matches && term !== '') {{

                let parent = item.parentElement;

                while (parent) {{

                    if (parent.classList.contains('location-children')) {{

                        parent.classList.remove('collapsed');

                        const toggle = parent.previousElementSibling?.querySelector('.location-toggle');

                        if (toggle) toggle.textContent = '▼';

                    }}

                    parent = parent.parentElement;

                }}

            }}

        }} else {{

            item.classList.add('hidden');

        }}

    }});

}}
