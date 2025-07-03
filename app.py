from flask import Flask, render_template_string, request
from sqlalchemy import create_engine, MetaData, Table, and_, select, distinct

app = Flask(__name__)
DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Reflect only the tables that exist
projects_table = Table('projects', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)

HTML = '''
<!doctype html>
<title>Project Search</title>
<h2>Project Search</h2>
<form method="post" id="searchForm">
  <label>Bottom Left (XMin/YMin): <input name="bottom_left"></label><br>
  <label>Top Right (XMax/YMax): <input name="top_right"></label><br>
  <label>Project UUID: <input name="uuid"></label><br>
  <div id="user_name_fields">
    <label>User Name: 
      <select name="user_name">
        <option value=""></option>
        {% for name in user_names %}
          <option value="{{ name }}">{{ name }}</option>
        {% endfor %}
      </select>
    </label>
  </div>
  <button type="button" onclick="addUserNameDropdown()">Add another user name</button><br>
  <label>Paper Size: <input name="paper_size"></label><br>
  <label>Scale: <input name="scale"></label><br>
  <input type="submit" value="Query">
</form>
<script>
function addUserNameDropdown() {
  var userNames = {{ user_names|tojson }};
  var div = document.getElementById('user_name_fields');
  var label = document.createElement('label');
  label.innerHTML = 'User Name: ';
  var select = document.createElement('select');
  select.name = 'user_name';
  var emptyOpt = document.createElement('option');
  emptyOpt.value = '';
  select.appendChild(emptyOpt);
  for (var i = 0; i < userNames.length; i++) {
    var opt = document.createElement('option');
    opt.value = userNames[i];
    opt.text = userNames[i];
    select.appendChild(opt);
  }
  label.appendChild(select);
  div.appendChild(label);
}
// Restore previous selections after reload (for POST)
window.onload = function() {
  var selected = {{ selected_user_names|tojson }};
  var userNames = {{ user_names|tojson }};
  var div = document.getElementById('user_name_fields');
  // Remove the initial dropdown if more than one selected
  if (selected.length > 1) {
    div.innerHTML = '';
  }
  for (var j = 0; j < selected.length; j++) {
    var label = document.createElement('label');
    label.innerHTML = 'User Name: ';
    var select = document.createElement('select');
    select.name = 'user_name';
    var emptyOpt = document.createElement('option');
    emptyOpt.value = '';
    select.appendChild(emptyOpt);
    for (var i = 0; i < userNames.length; i++) {
      var opt = document.createElement('option');
      opt.value = userNames[i];
      opt.text = userNames[i];
      if (userNames[i] == selected[j]) opt.selected = true;
      select.appendChild(opt);
    }
    label.appendChild(select);
    div.appendChild(label);
  }
}
</script>
{% if error %}
  <p style="color:red;">{{ error }}</p>
{% endif %}
{% if results is not none %}
  <h3>Project Results:</h3>
  {% if results %}
    <table border="1" cellpadding="5">
      <tr><th>UUID</th><th>Project Name</th><th>User Name</th><th>Date</th><th>File Location</th><th>Paper Size</th><th>Scale</th></tr>
      {% for proj in results %}
        <tr>
          <td>{{ proj.uuid }}</td>
          <td>{{ proj.project_name }}</td>
          <td>{{ proj.user_name }}</td>
          <td>{{ proj.date }}</td>
          <td>{{ proj.file_location }}</td>
          <td>{{ proj.paper_size }}</td>
          <td>{{ proj.scale }}</td>
        </tr>
      {% endfor %}
    </table>
  {% else %}
    <p>No matching projects found.</p>
  {% endif %}
{% endif %}
<hr>
<h2>All Projects</h2>
<table border="1" cellpadding="5">
  <tr>
    <th>UUID</th><th>Project Name</th><th>User Name</th><th>Date</th><th>File Location</th><th>Paper Size</th><th>Scale</th>
  </tr>
  {% for proj in projects %}
  <tr>
    <td>{{ proj.uuid }}</td>
    <td>{{ proj.project_name }}</td>
    <td>{{ proj.user_name }}</td>
    <td>{{ proj.date }}</td>
    <td>{{ proj.file_location }}</td>
    <td>{{ proj.paper_size }}</td>
    <td>{{ proj.scale }}</td>
  </tr>
  {% endfor %}
</table>

<h2>All Areas</h2>
<table border="1" cellpadding="5">
  <tr>
    <th>ID</th><th>Project UUID</th><th>XMin</th><th>YMin</th><th>XMax</th><th>YMax</th>
  </tr>
  {% for area in areas %}
  <tr>
    <td>{{ area.id }}</td>
    <td>{{ area.project_id }}</td>
    <td>{{ area.xmin }}</td>
    <td>{{ area.ymin }}</td>
    <td>{{ area.xmax }}</td>
    <td>{{ area.ymax }}</td>
  </tr>
  {% endfor %}
</table>
'''

def parse_point(s):
    try:
        s = s.strip()
        if '/' in s:
            x_str, y_str = s.split('/')
        elif ',' in s:
            x_str, y_str = s.split(',')
        else:
            return None
        return float(x_str), float(y_str)
    except Exception:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    # Query unique user names for the dropdown
    with engine.connect() as conn:
        user_names = [row[0] for row in conn.execute(select(projects_table.c.user_name).distinct())]
    selected_user_names = []
    if request.method == 'POST':
        filters = []
        join_areas = False
        # Parse spatial box
        bottom_left = request.form.get('bottom_left', '').strip()
        top_right = request.form.get('top_right', '').strip()
        if bottom_left and top_right:
            bl = parse_point(bottom_left)
            tr = parse_point(top_right)
            if not bl or not tr:
                error = 'Invalid input format. Please use X/Y or X,Y for both points.'
            else:
                xmin, ymin = bl
                xmax, ymax = tr
                if xmin >= xmax or ymin >= ymax:
                    error = 'Bottom Left must be southwest (smaller X and Y) of Top Right. Please check your input.'
                else:
                    join_areas = True
                    filters.append(areas_table.c.xmin < xmax)
                    filters.append(areas_table.c.xmax > xmin)
                    filters.append(areas_table.c.ymin < ymax)
                    filters.append(areas_table.c.ymax > ymin)
        # Parse other filters
        uuid = request.form.get('uuid', '').strip()
        if uuid:
            filters.append(projects_table.c.uuid == uuid)
        user_name_list = request.form.getlist('user_name')
        selected_user_names = [n for n in user_name_list if n]
        if selected_user_names:
            filters.append(projects_table.c.user_name.in_(selected_user_names))
        paper_size = request.form.get('paper_size', '').strip()
        if paper_size:
            filters.append(projects_table.c.paper_size == paper_size)
        scale = request.form.get('scale', '').strip()
        if scale:
            try:
                scale_val = float(scale)
                filters.append(projects_table.c.scale == scale_val)
            except ValueError:
                error = 'Scale must be a number.'
        if error is None:
            with engine.connect() as conn:
                if join_areas:
                    # Join projects and areas, filter by area, select distinct projects
                    join_stmt = projects_table.join(areas_table, projects_table.c.uuid == areas_table.c.project_id)
                    sel = select(*projects_table.c).select_from(join_stmt).where(and_(*filters)).distinct()
                    results = [dict(row) for row in conn.execute(sel)]
                elif filters:
                    # Only project filters
                    sel = select(*projects_table.c).where(and_(*filters))
                    results = [dict(row) for row in conn.execute(sel)]
                else:
                    results = []
    with engine.connect() as conn:
        projects = conn.execute(projects_table.select()).fetchall()
        areas = conn.execute(areas_table.select()).fetchall()
    return render_template_string(HTML, results=results, error=error, projects=projects, areas=areas, user_names=user_names, selected_user_names=selected_user_names)

if __name__ == '__main__':
    app.run(debug=True) 