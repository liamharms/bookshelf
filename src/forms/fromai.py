from wtforms import SelectField
from wtforms.widgets import Select
from markupsafe import Markup

class LocationTreeWidget:
    """Custom widget that renders a searchable tree select for locations"""
    
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)
        
        # Get the selected value
        selected_value = kwargs.pop('value', field.data or '')
        
        # Build the HTML
        html = [f'<div class="location-tree-select-container">']
        
        # Search input
        html.append(f'''
            <input type="text" 
                   class="form-control mb-2" 
                   id="{field.id}_search" 
                   placeholder="Search locations..."
                   onkeyup="filterLocations_{field.id}(this.value)">
        ''')
        
        # Hidden input to store the actual value
        html.append(f'''
            <input type="hidden" 
                   id="{kwargs['id']}" 
                   name="{kwargs['name']}" 
                   value="{selected_value}">
        ''')
        
        # Tree container
        html.append(f'<div class="location-tree-select" id="{field.id}_tree">')
        html.append('<ul class="location-tree-list">')
        
        # Render the tree
        html.append(self._render_tree(field.choices, selected_value, field.id))
        
        html.append('</ul>')
        html.append('</div>')
        
        # Add CSS
        html.append(self._get_css(field.id))
        
        # Add JavaScript
        html.append(self._get_js(field.id))
        
        html.append('</div>')
        
        return Markup(''.join(html))
    
    def _render_tree(self, choices, selected_value, field_id, level=0):
        """Recursively render the location tree"""
        html = []
        
        for value, label, children in choices:
            indent = level * 20
            has_children = len(children) > 0
            is_selected = str(value) == str(selected_value)
            
            html.append(f'<li class="location-tree-item" style="padding-left: {indent}px;" data-location-id="{value}" data-location-name="{label}">')
            html.append('<div class="location-tree-node">')
            
            # Toggle button for parents
            if has_children:
                html.append(f'''
                    <button type="button" 
                            class="location-toggle" 
                            onclick="toggleLocationNode_{field_id}(this)">▼</button>
                ''')
            else:
                html.append('<span class="location-toggle-spacer"></span>')
            
            # Radio button for selection
            checked = 'checked' if is_selected else ''
            html.append(f'''
                <input type="radio" 
                       name="{field_id}_radio" 
                       value="{value}" 
                       id="{field_id}_option_{value}"
                       {checked}
                       onchange="selectLocation_{field_id}({value})">
            ''')
            
            # Label
            html.append(f'<label for="{field_id}_option_{value}" class="location-label">{label}</label>')
            
            html.append('</div>')
            
            # Render children
            if has_children:
                html.append('<ul class="location-children">')
                html.append(self._render_tree(children, selected_value, field_id, level + 1))
                html.append('</ul>')
            
            html.append('</li>')
        
        return ''.join(html)
    
    def _get_css(self, field_id):
        return f'''
        <style>
            .location-tree-select-container {{
                border: 1px solid #ced4da;
                border-radius: 0.25rem;
                padding: 10px;
                background-color: #fff;
            }}
            
            .location-tree-select {{
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                background-color: #f8f9fa;
            }}
            
            .location-tree-list {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            
            .location-tree-item {{
                margin: 2px 0;
            }}
            
            .location-tree-node {{
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 4px;
                border-radius: 3px;
            }}
            
            .location-tree-node:hover {{
                background-color: #e9ecef;
            }}
            
            .location-toggle {{
                border: none;
                background: none;
                cursor: pointer;
                font-size: 12px;
                width: 20px;
                height: 20px;
                padding: 0;
                color: #6c757d;
            }}
            
            .location-toggle:hover {{
                color: #495057;
            }}
            
            .location-toggle-spacer {{
                display: inline-block;
                width: 20px;
            }}
            
            .location-label {{
                cursor: pointer;
                margin: 0;
                user-select: none;
                flex-grow: 1;
            }}
            
            .location-children {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            
            .location-children.collapsed {{
                display: none;
            }}
            
            .location-tree-item.hidden {{
                display: none;
            }}
        </style>
        '''
    
    def _get_js(self, field_id):
        return f'''
        <script>
            function toggleLocationNode_{field_id}(button) {{
                const item = button.closest('.location-tree-item');
                const children = item.querySelector('.location-children');
                
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
        </script>
        '''


class LocationTreeSelectField(SelectField):
    widget = LocationTreeWidget()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def build_location_tree_choices(locations):
    """
    Helper function to build hierarchical choices from Location query results.
    
    Args:
        locations: List of Location objects from database
        
    Returns:
        List of tuples in format: (value, label, children)
        where children is a list of the same format
    
    Usage:
        locations = Location.query.all()
        form.location_id.choices = build_location_tree_choices(locations)
    """
    
    def build_tree(parent_id=None):
        """Recursively build tree structure"""
        result = []
        for loc in locations:
            if loc.parent_id == parent_id:
                children = build_tree(loc.id)
                
                # Build the label with parent path
                label = loc.name
                if parent_id is not None:
                    parent = next((l for l in locations if l.id == loc.parent_id), None)
                    if parent:
                        # You can customize this to show the full path
                        label = f"{loc.name}"
                
                result.append((loc.id, label, children))
        return result
    
    # Start with root locations (those without a parent)
    tree = build_tree(None)
    
    # Add empty option at the beginning
    tree.insert(0, ('', '-- Select Location --', []))
    
    return tree


# Example form usage:
"""
from flask_wtf import FlaskForm

class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    location_id = LocationTreeSelectField('Location', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

# In your route:
@app.route('/book/add', methods=['GET', 'POST'])
def add_book():
    form = BookForm()
    
    # Populate location choices
    locations = Location.query.all()
    form.location_id.choices = build_location_tree_choices(locations)
    
    if form.validate_on_submit():
        # form.location_id.data will contain the selected location ID
        book = Book(
            title=form.title.data,
            location_id=form.location_id.data
        )
        db.session.add(book)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('add_book.html', form=form)
"""