from flask import Flask, render_template_string, request, url_for, send_file, redirect
from sqlalchemy import create_engine, MetaData, Table, and_, select, distinct, func, text, or_
import os
import glob2
from datetime import datetime
import shutil

app = Flask(__name__)

# Custom filter for datetime formatting
@app.template_filter('datetime')
def datetime_filter(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')



DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Reflect only the tables that exist
projects_table = Table('projects', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)

HTML = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Search</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f4f7f6;
            color: #333;
            line-height: 1.6;
        }
        
        .header-footer {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header-footer:last-of-type {
            margin-top: 30px;
            margin-bottom: 0;
        }
        
        .logo-section {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .logo {
            width: 40px;
            height: 40px;
            background: #e74c3c;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
            color: white;
        }
        
        .company-info {
            font-size: 14px;
        }
        
        .copyright {
            font-size: 12px;
            opacity: 0.9;
        }

        h2, h3 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }

        form {
            background-color: #ffffff;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            display: grid;
            gap: 15px;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }
        
        /* Force specific fields to be on their own line */
        form label:nth-child(3) {  /* Project UUID */
            grid-column: 1 / -1;
        }

        form label {
            display: flex;
            flex-direction: column;
            font-weight: bold;
            margin-bottom: 5px;
        }

        form input[type="text"],
        form select {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1em;
            width: 100%;
            box-sizing: border-box;
        }

        form button,
        form input[type="submit"] {
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s ease;
            margin-top: 10px;
        }

        form button:hover,
        form input[type="submit"]:hover {
            background-color: #2980b9;
        }

        #user_name_fields {
            grid-column: span 2;
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: flex-end;
        }

        #user_name_fields label {
            flex: 1 1 auto;
            min-width: 200px;
        }

        .error {
            color: red;
            background-color: #ffe5e5;
            border: 1px solid red;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background-color: #ffffff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        th, td {
            padding: 12px 15px;
            border: 1px solid #e0e0e0;
            text-align: left;
        }

        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 1;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        tr:hover {
            background-color: #f1f1f1;
        }

        p {
            margin-top: 15px;
            font-style: italic;
            color: #555;
        }

        hr {
            border: 0;
            height: 1px;
            background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));
            margin: 40px 0;
        }

        .pagination {
            margin-top: 20px;
            text-align: center;
        }

        .pagination a, .pagination span {
            display: inline-block;
            padding: 8px 16px;
            margin: 0 4px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-decoration: none;
            color: #3498db;
            background-color: #fff;
            transition: background-color 0.3s, color 0.3s;
        }

        .pagination a:hover {
            background-color: #3498db;
            color: white;
        }

        .pagination span.current-page {
            background-color: #3498db;
            color: white;
            border-color: #3498db;
            font-weight: bold;
        }

        .pagination span.disabled {
            color: #bbb;
            cursor: not-allowed;
        }
        .filter-form input[type="text"] {
            width: calc(100% - 10px); /* Adjust width for padding */
            padding: 5px;
            margin: 2px 0;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 3px;
        }
        
        .filter-form input[type="date"] {
            padding: 3px;
            margin: 1px 0;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 3px;
            font-size: 0.8em;
        }
        .table-container {
            overflow-x: auto; /* Enable horizontal scrolling for tables */
        }

        /* Date range styling */
        #date_range_fields {
            grid-column: span 2;
        }
        
        #date_range_fields input[type="text"] {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1em;
            width: 100%;
            box-sizing: border-box;
        }
        
        #date_range_fields span {
            font-weight: bold;
            color: #666;
        }

        /* Custom size fields styling */
        #custom_size_fields {
            grid-column: span 2;
            display: flex;
            gap: 15px;
            align-items: flex-end;
        }

        #custom_size_fields label {
            flex: 1 1 auto;
            min-width: 200px;
        }

        #custom_size_fields input[type="number"] {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1em;
            width: 100%;
            box-sizing: border-box;
        }

        .full-width-row {
            grid-column: 1 / -1;
            width: 100%;
            display: flex;
            align-items: flex-end;
            margin-top: 10px;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            form {
                grid-template-columns: 1fr;
            }
            #user_name_fields {
                grid-column: span 1;
                flex-direction: column;
            }
            #date_range_fields {
                grid-column: span 1;
            }
            #custom_size_fields {
                grid-column: span 1;
                flex-direction: column;
            }
        }
        .center-query-btn {
            grid-column: 1 / -1;
            width: 100%;
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        .center-query-btn input[type="submit"] {
            min-width: 200px;
        }
        
        .center-query-btn button[type="button"] {
            min-width: 200px;
            background-color: #e74c3c;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            transition: background-color 0.3s ease;
            margin-left: 10px;
        }
        
        .center-query-btn button[type="button"]:hover {
            background-color: #c0392b;
        }
        
        /* Actions column styling */
        .actions-column {
            min-width: 120px;
        }
        
        .actions-column a {
            display: inline-block;
            margin: 2px 0;
            padding: 4px 8px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            font-size: 0.9em;
        }
        
        .actions-column a:hover {
            background-color: #2980b9;
        }

        .actions-column form {
            display: inline;
            margin: 0;
            padding: 0;
        }
        .actions-column button[type="submit"] {
            display: inline-block;
            margin: 2px 0;
            padding: 4px 8px;
            background-color: #e74c3c;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            font-size: 0.9em;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
            vertical-align: middle;
        }
        .actions-column button[type="submit"]:hover {
            background-color: #c0392b;
        }
    </style>
</head>
<body>
    <!-- Header with Logo and Copyright -->
    <div class="header-footer">
        <div class="logo-section">
            <div class="logo">
                <img src="{{ url_for('static', filename='rocket.jpg') }}" alt="Rocket Logo" style="width: 36px; height: 36px; object-fit: contain; border-radius: 50%; background: white;">
            </div>
            <div class="company-info">
                <strong>ARCgis PRO DataBase</strong><br>
                <span style="font-size: 11px;">פרוייקט שימור הידע של (נוסיף שיתאפשר)</span><br>
                <span class="copyright">@Rocket Team Production</span>
            </div>
        </div>
        <div class="copyright">
            Version 1.0 | Spatial Database Management System
        </div>
    </div>
    
    <h2>Project Search</h2>
    <form method="post" id="searchForm">
      <label>Bottom Left (XMin/YMin): <input name="bottom_left" type="text" placeholder="e.g., 10.5/20.1" value="{{ request.form.bottom_left if request.form.bottom_left else '' }}"></label>
      <label>Top Right (XMax/YMax): <input name="top_right" type="text" placeholder="e.g., 30.0/40.8" value="{{ request.form.top_right if request.form.top_right else '' }}"></label>
      <label>Project UUID: <input name="uuid" type="text" placeholder="e.g., a1b2c3d4-e5f6-7890-1234-567890abcdef" value="{{ request.form.uuid if request.form.uuid else '' }}"></label>
      <div id="user_name_fields" style="grid-column: 1 / -1;">
        <label>User Name:
          <select name="user_name">
            <option value=""></option>
            {% for name in user_names %}
              <option value="{{ name }}">{{ name }}</option>
            {% endfor %}
          </select>
        </label>
      </div>
      <button type="button" onclick="addUserNameDropdown()">Add another user name</button>
      <div class="full-width-row" id="paper_size_row">
        <label style="margin-bottom:0;">Paper Size:
          <select name="paper_size" id="paper_size_select" onchange="toggleCustomSize()">
            <option value="">Select Paper Size</option>
            <option value="A0 (Portrait)" {% if request.form.paper_size == 'A0 (Portrait)' %}selected{% endif %}>A0 (Portrait)</option>
            <option value="A0 (Landscape)" {% if request.form.paper_size == 'A0 (Landscape)' %}selected{% endif %}>A0 (Landscape)</option>
            <option value="A1 (Portrait)" {% if request.form.paper_size == 'A1 (Portrait)' %}selected{% endif %}>A1 (Portrait)</option>
            <option value="A1 (Landscape)" {% if request.form.paper_size == 'A1 (Landscape)' %}selected{% endif %}>A1 (Landscape)</option>
            <option value="A2 (Portrait)" {% if request.form.paper_size == 'A2 (Portrait)' %}selected{% endif %}>A2 (Portrait)</option>
            <option value="A2 (Landscape)" {% if request.form.paper_size == 'A2 (Landscape)' %}selected{% endif %}>A2 (Landscape)</option>
            <option value="A3 (Portrait)" {% if request.form.paper_size == 'A3 (Portrait)' %}selected{% endif %}>A3 (Portrait)</option>
            <option value="A3 (Landscape)" {% if request.form.paper_size == 'A3 (Landscape)' %}selected{% endif %}>A3 (Landscape)</option>
            <option value="A4 (Portrait)" {% if request.form.paper_size == 'A4 (Portrait)' %}selected{% endif %}>A4 (Portrait)</option>
            <option value="A4 (Landscape)" {% if request.form.paper_size == 'A4 (Landscape)' %}selected{% endif %}>A4 (Landscape)</option>
            <option value="A5 (Portrait)" {% if request.form.paper_size == 'A5 (Portrait)' %}selected{% endif %}>A5 (Portrait)</option>
            <option value="A5 (Landscape)" {% if request.form.paper_size == 'A5 (Landscape)' %}selected{% endif %}>A5 (Landscape)</option>
            <option value="B0 (Portrait)" {% if request.form.paper_size == 'B0 (Portrait)' %}selected{% endif %}>B0 (Portrait)</option>
            <option value="B0 (Landscape)" {% if request.form.paper_size == 'B0 (Landscape)' %}selected{% endif %}>B0 (Landscape)</option>
            <option value="custom" {% if request.form.paper_size == 'custom' %}selected{% endif %}>Custom Size</option>
          </select>
        </label>
        <div id="custom_size_fields" style="display: none; margin-left: 15px; flex: 0 0 auto;">
          <label style="margin-bottom:0;">Custom Height (cm): <input name="custom_height" type="number" step="0.1" placeholder="e.g., 29.7" value="{{ request.form.custom_height if request.form.custom_height else '' }}"></label>
          <label style="margin-bottom:0; margin-left: 10px;">Custom Width (cm): <input name="custom_width" type="number" step="0.1" placeholder="e.g., 21.0" value="{{ request.form.custom_width if request.form.custom_width else '' }}"></label>
        </div>
      </div>
      <label>Scale: <input name="scale" type="text" placeholder="e.g., 1000" value="{{ request.form.scale if request.form.scale else '' }}"></label>
      <div id="date_range_fields">
        <label>Date Range:
          <div style="display: flex; gap: 10px; align-items: center;">
            <input name="date_from" type="text" placeholder="DD/MM/YYYY (e.g., 09/07/2025)" value="{{ request.form.date_from if request.form.date_from else '' }}" style="flex: 1;" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}">
            <span>to</span>
            <input name="date_to" type="text" placeholder="DD/MM/YYYY (e.g., 25/12/2025)" value="{{ request.form.date_to if request.form.date_to else '' }}" style="flex: 1;" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}">
          </div>
        </label>
      </div>
      <div class="center-query-btn">
        <input type="submit" value="Query">
        <button type="button" onclick="resetForm()">Reset Query</button>
      </div>
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

    function toggleCustomSize() {
      var paperSizeSelect = document.getElementById('paper_size_select');
      var customFields = document.getElementById('custom_size_fields');
      
      if (paperSizeSelect.value === 'custom') {
        customFields.style.display = 'block';
      } else {
        customFields.style.display = 'none';
      }
    }

    function resetForm() {
      // Reset all form inputs
      document.getElementById('searchForm').reset();
      
      // Hide custom size fields
      document.getElementById('custom_size_fields').style.display = 'none';
      
      // Clear any additional user name dropdowns (keep only the first one)
      var userNamesDiv = document.getElementById('user_name_fields');
      var labels = userNamesDiv.querySelectorAll('label');
      for (var i = 1; i < labels.length; i++) {
        labels[i].remove();
      }
      
      // Reset the first user name dropdown
      if (labels.length > 0) {
        var firstSelect = labels[0].querySelector('select');
        if (firstSelect) {
          firstSelect.value = '';
        }
      }
    }

    function copyPath(path) {
      // Create a temporary textarea element
      var textarea = document.createElement('textarea');
      textarea.value = path;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      
      // Select and copy the text
      textarea.select();
      document.execCommand('copy');
      
      // Remove the temporary element
      document.body.removeChild(textarea);
      
      // Show a brief notification
      var notification = document.createElement('div');
      notification.textContent = 'Path copied to clipboard!';
      notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #27ae60; color: white; padding: 10px 15px; border-radius: 5px; z-index: 10000; font-size: 14px;';
      document.body.appendChild(notification);
      
      // Remove notification after 2 seconds
      setTimeout(function() {
        if (notification.parentNode) {
          notification.parentNode.removeChild(notification);
        }
      }, 2000);
    }

    // Function to get a URL parameter
    function getUrlParameter(name) {
        name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
        var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
        var results = regex.exec(location.search);
        return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
    };

    window.onload = function() {
      var selected = {{ selected_user_names|tojson }};
      var userNames = {{ user_names|tojson }};
      var div = document.getElementById('user_name_fields');

      // Clear existing dropdowns if we are re-populating with multiple or if initial is empty and we have selections
      if (selected.length > 1 || (selected.length === 1 && selected[0] !== '' && div.querySelector('select').value === '')) {
        div.innerHTML = '';
      } else if (selected.length === 1 && selected[0] !== '') {
          // If only one selected and it's not empty, just set its value and return
          var firstSelect = div.querySelector('select');
          if (firstSelect) {
             firstSelect.value = selected[0];
          }
          // Do not return here if you want other window.onload logic to run
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

      // Add hidden input for scroll position to each filter form
      const projectsFilterForm = document.getElementById('projectsFilterForm');
      if (projectsFilterForm) {
          let scrollInput = document.createElement('input');
          scrollInput.type = 'hidden';
          scrollInput.name = 'scroll_pos';
          scrollInput.id = 'projects_scroll_pos';
          projectsFilterForm.appendChild(scrollInput);

          projectsFilterForm.addEventListener('submit', function() {
              document.getElementById('projects_scroll_pos').value = window.scrollY;
          });
      }

      const areasFilterForm = document.getElementById('areasFilterForm');
      if (areasFilterForm) {
          let scrollInput = document.createElement('input');
          scrollInput.type = 'hidden';
          scrollInput.name = 'scroll_pos';
          scrollInput.id = 'areas_scroll_pos';
          areasFilterForm.appendChild(scrollInput);

          areasFilterForm.addEventListener('submit', function() {
              document.getElementById('areas_scroll_pos').value = window.scrollY;
          });
      }

      // Add event listeners to filter inputs for submitting on change (or enter key)
      document.querySelectorAll('.filter-input').forEach(input => {
        input.addEventListener('change', function() {
          // Ensure the hidden scroll input is updated before submission
          if (this.closest('form') && this.closest('form').id === 'projectsFilterForm') {
              document.getElementById('projects_scroll_pos').value = window.scrollY;
          } else if (this.closest('form') && this.closest('form').id === 'areasFilterForm') {
              document.getElementById('areas_scroll_pos').value = window.scrollY;
          }
          this.form.submit();
        });
        input.addEventListener('keypress', function(event) {
          if (event.key === 'Enter') {
            event.preventDefault(); // Prevent default Enter key behavior (form submission)
            // Ensure the hidden scroll input is updated before submission
            if (this.closest('form') && this.closest('form').id === 'projectsFilterForm') {
                document.getElementById('projects_scroll_pos').value = window.scrollY;
            } else if (this.closest('form') && this.closest('form').id === 'areasFilterForm') {
                document.getElementById('areas_scroll_pos').value = window.scrollY;
            }
            this.form.submit();
          }
        });
      });

      // Restore scroll position after the page loads
      const scroll_pos = getUrlParameter('scroll_pos');
      if (scroll_pos) {
          window.scrollTo(0, parseInt(scroll_pos));
      }

      // Initialize custom size fields state
      toggleCustomSize();
    }
    </script>
    {% if error %}
      <p class="error">{{ error }}</p>
    {% endif %}
    {% if results is not none %}
      <h3>Project Results:</h3>
      {% if results %}
        <div class="table-container">
            <table border="1" cellpadding="5">
              <tr><th>UUID</th><th>Project Name</th><th>User Name</th><th>Date</th><th>File Location</th><th>Paper Size</th><th>Scale</th><th class="actions-column">Actions</th></tr>
              {% for proj in results %}
                {% if proj and proj.uuid %}
                <tr>
                  <td>{{ proj.uuid }}</td>
                  <td>{{ proj.project_name }}</td>
                  <td>{{ proj.user_name }}</td>
                  <td>{{ proj.date }}</td>
                  <td><a href="file:///{{ proj.abs_file_location_url }}" target="_blank">{{ proj.file_location }}</a></td>
                  <td>{{ proj.paper_size }}</td>
                  <td>{{ proj.scale }}</td>
                  <td class="actions-column">
                    <!-- DEBUG: {{ proj.uuid }} -->
                    {% if proj.view_file_path %}{% if proj.file_count == 1 %}<a href="#" onclick="showFileModal('{{ url_for('view_file', rel_path=proj.view_file_path) }}','{{ proj.view_file_type }}'); return false">View</a><a href="#" onclick="copyPath('{{ proj.file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Path</a>{% else %}<a href="#" onclick="showAllFilesModal('{{ proj.uuid }}'); return false" data-files='{{ proj.all_files|tojson|safe }}'>View ({{ proj.file_count }})</a><a href="#" onclick="copyPath('{{ proj.file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Path</a>{% endif %}{% else %}<a href="#" onclick="copyPath('{{ proj.file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Path</a>{% endif %}<form method="post" action="{{ url_for('delete_project', uuid=proj.uuid|e) }}" style="display:inline;" onsubmit="return confirm('Are you sure you want to delete this project?');"><button type="submit">Delete</button></form></td>
                </tr>
                {% endif %}
              {% endfor %}
            </table>
        </div>
      {% else %}
        <p>No matching projects found.</p>
      {% endif %}
    {% endif %}
    <hr>
    <h2>All Projects</h2>
    <div class="table-container">
        <form method="get" id="projectsFilterForm">
            <input type="hidden" name="page" value="{{ projects_current_page }}">
            <input type="hidden" name="per_page" value="{{ projects_per_page }}">
            <table border="1" cellpadding="5">
              <thead>
                <tr>
                  <th>UUID <br> <input type="text" name="projects_uuid_filter" class="filter-input" value="{{ projects_filters.uuid_filter }}" placeholder="Filter UUID"></th>
                  <th>Project Name <br> <input type="text" name="projects_project_name_filter" class="filter-input" value="{{ projects_filters.project_name_filter }}" placeholder="Filter Name"></th>
                  <th>User Name <br> <input type="text" name="projects_user_name_filter" class="filter-input" value="{{ projects_filters.user_name_filter }}" placeholder="Filter User"></th>
                  <th>Date <br> 
                    <input type="text" name="projects_date_filter" class="filter-input" value="{{ projects_filters.date_filter }}" placeholder="Filter Date" style="width: 100%; margin-bottom: 2px;">
                    <input type="text" name="projects_date_from_filter" class="filter-input" value="{{ projects_filters.date_from_filter }}" placeholder="DD/MM/YYYY" style="width: 48%; font-size: 0.8em;" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}">
                    <input type="text" name="projects_date_to_filter" class="filter-input" value="{{ projects_filters.date_to_filter }}" placeholder="DD/MM/YYYY" style="width: 48%; font-size: 0.8em; margin-left: 2%;" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}">
                  </th>
                  <th>File Location <br> <input type="text" name="projects_file_location_filter" class="filter-input" value="{{ projects_filters.file_location_filter }}" placeholder="Filter Location"></th>
                  <th>Paper Size <br> <input type="text" name="projects_paper_size_filter" class="filter-input" value="{{ projects_filters.paper_size_filter }}" placeholder="Filter Size"></th>
                  <th>Scale <br> <input type="text" name="projects_scale_filter" class="filter-input" value="{{ projects_filters.scale_filter }}" placeholder="Filter Scale"></th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {% for proj in projects %}
                  {% if proj and proj.uuid %}
                  <tr>
                    <td>{{ proj.uuid }}</td>
                    <td>{{ proj.project_name }}</td>
                    <td>{{ proj.user_name }}</td>
                    <td>{{ proj.date }}</td>
                    <td>{{ proj.file_location }}</td>
                    <td>{{ proj.paper_size }}</td>
                    <td>{{ proj.scale }}</td>
                    <td class="actions-column">
                      <!-- DEBUG: {{ proj.uuid }} -->
                      {% if proj.view_file_path %}{% if proj.file_count == 1 %}<a href="#" onclick="showFileModal('{{ url_for('view_file', rel_path=proj.view_file_path) }}','{{ proj.view_file_type }}'); return false">View</a><a href="#" onclick="copyPath('{{ proj.file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Path</a>{% else %}<a href="#" onclick="showAllFilesModal('{{ proj.uuid }}'); return false" data-files='{{ proj.all_files|tojson|safe }}'>View ({{ proj.file_count }})</a><a href="#" onclick="copyPath('{{ proj.file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Path</a>{% endif %}{% else %}<a href="#" onclick="copyPath('{{ proj.file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Path</a>{% endif %}</td>
                  </tr>
                  {% endif %}
                {% endfor %}
              </tbody>
            </table>
        </form>
    </div>
    <div class="pagination">
        {% if projects_current_page > 1 %}
            <a href="{{ url_for('index', page=projects_current_page - 1, per_page=projects_per_page, **projects_filters) }}">Previous</a>
        {% else %}
            <span class="disabled">Previous</span>
        {% endif %}

        {% for p in range(1, projects_total_pages + 1) %}
            {% if p == projects_current_page %}
                <span class="current-page">{{ p }}</span>
            {% else %}
                <a href="{{ url_for('index', page=p, per_page=projects_per_page, **projects_filters) }}">{{ p }}</a>
            {% endif %}
        {% endfor %}

        {% if projects_current_page < projects_total_pages %}
            <a href="{{ url_for('index', page=projects_current_page + 1, per_page=projects_per_page, **projects_filters) }}">Next</a>
        {% else %}
            <span class="disabled">Next</span>
        {% endif %}
        <br>
        <label>Items per page:
            <select onchange="window.location.href = '{{ url_for('index', **projects_filters) }}' + '&per_page=' + this.value">
                {% for size in [5, 10, 20, 50] %}
                    <option value="{{ size }}" {% if projects_per_page == size %}selected{% endif %}>{{ size }}</option>
                {% endfor %}
            </select>
        </label>
    </div>

    <h2>All Areas</h2>
    <div class="table-container">
        <form method="get" id="areasFilterForm">
            <input type="hidden" name="areas_page" value="{{ areas_current_page }}">
            <input type="hidden" name="areas_per_page" value="{{ areas_per_page }}">
            <table border="1" cellpadding="5">
              <thead>
                <tr>
                  <th>ID <br> <input type="text" name="areas_id_filter" class="filter-input" value="{{ areas_filters.id_filter }}" placeholder="Filter ID"></th>
                  <th>Project UUID <br> <input type="text" name="areas_project_id_filter" class="filter-input" value="{{ areas_filters.project_id_filter }}" placeholder="Filter UUID"></th>
                  <th>XMin <br> <input type="text" name="areas_xmin_filter" class="filter-input" value="{{ areas_filters.xmin_filter }}" placeholder="Filter XMin"></th>
                  <th>YMin <br> <input type="text" name="areas_ymin_filter" class="filter-input" value="{{ areas_filters.ymin_filter }}" placeholder="Filter YMin"></th>
                  <th>XMax <br> <input type="text" name="areas_xmax_filter" class="filter-input" value="{{ areas_filters.xmax_filter }}" placeholder="Filter XMax"></th>
                  <th>YMax <br> <input type="text" name="areas_ymax_filter" class="filter-input" value="{{ areas_filters.ymax_filter }}" placeholder="Filter YMax"></th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {% for area in areas %}
                <tr>
                  <td>{{ area.id }}</td>
                  <td>{{ area.project_id }}</td>
                  <td>{{ area.xmin }}</td>
                  <td>{{ area.ymin }}</td>
                  <td>{{ area.xmax }}</td>
                  <td>{{ area.ymax }}</td>
                  <td class="actions-column">
                    {% if area.project_view_file_path %}
                      {% if area.project_file_count == 1 %}
                        <a href="#" onclick="showFileModal('{{ url_for('view_file', rel_path=area.project_view_file_path) }}','{{ area.project_view_file_type }}'); return false">View Project</a>
                        <a href="#" onclick="copyPath('{{ area.project_file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Project Path</a>
                      {% else %}
                        <a href="#" onclick="showAllFilesModal('{{ area.project_id }}'); return false" data-files='{{ area.project_all_files|tojson|safe }}'>View Project ({{ area.project_file_count }})</a>
                        <a href="#" onclick="copyPath('{{ area.project_file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Project Path</a>
                      {% endif %}
                    {% else %}
                      <a href="#" onclick="copyPath('{{ area.project_file_location|safe }}'); return false" style="background-color: #27ae60;">Copy Project Path</a>
                    {% endif %}
                  </td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
        </form>
    </div>
    <div class="pagination">
        {% if areas_current_page > 1 %}
            <a href="{{ url_for('index', areas_page=areas_current_page - 1, areas_per_page=areas_per_page, **areas_filters) }}">Previous</a>
        {% else %}
            <span class="disabled">Previous</span>
        {% endif %}

        {% for p in range(1, areas_total_pages + 1) %}
            {% if p == areas_current_page %}
                <span class="current-page">{{ p }}</span>
            {% else %}
                <a href="{{ url_for('index', areas_page=p, areas_per_page=areas_per_page, **areas_filters) }}">{{ p }}</a>
            {% endif %}
        {% endfor %}

        {% if areas_current_page < areas_total_pages %}
            <a href="{{ url_for('index', areas_page=areas_current_page + 1, areas_per_page=areas_per_page, **areas_filters) }}">Next</a>
        {% else %}
            <span class="disabled">Next</span>
        {% endif %}
        <br>
        <label>Items per page:
            <select onchange="window.location.href = '{{ url_for('index', **areas_filters) }}' + '&areas_per_page=' + this.value">
                {% for size in [5, 10, 20, 50] %}
                    <option value="{{ size }}" {% if areas_per_page == size %}selected{% endif %}>{{ size }}</option>
                {% endfor %}
            </select>
        </label>
    </div>
    <div id="fileModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.8); z-index:9999; align-items:center; justify-content:center;">
      <div id="fileModalContent" style="position:relative; background:#fff; padding:20px; border-radius:8px; max-width:90vw; max-height:90vh; overflow:auto;">
        <button onclick="closeFileModal()" style="position:absolute; top:10px; right:10px; z-index:10000;">Close</button>
        <div id="fileModalBody"></div>
      </div>
    </div>
    
    <!-- Gallery Modal for All Files -->
    <div id="galleryModal" style="display:none; position:fixed; top:0; left:0; width:100vw; height:100vh; background:rgba(0,0,0,0.9); z-index:10000; align-items:center; justify-content:center;">
      <div id="galleryModalContent" style="position:relative; background:#fff; padding:20px; border-radius:8px; max-width:95vw; max-height:95vh; overflow:hidden; display:flex; flex-direction:column;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
          <h3 id="galleryTitle" style="margin:0; color:#333;">Project Files</h3>
          <button onclick="closeGalleryModal()" style="background:#e74c3c; color:white; border:none; padding:8px 12px; border-radius:4px; cursor:pointer;">Close</button>
        </div>
        
        <div id="galleryContainer" style="flex:1; display:flex; align-items:center; justify-content:center; position:relative;">
          <!-- Navigation Arrows -->
          <button id="prevBtn" onclick="previousFile()" style="position:absolute; left:10px; top:50%; transform:translateY(-50%); background:rgba(0,0,0,0.7); color:white; border:none; padding:15px 10px; border-radius:50%; cursor:pointer; font-size:18px; z-index:10001;">‹</button>
          <button id="nextBtn" onclick="nextFile()" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); background:rgba(0,0,0,0.7); color:white; border:none; padding:15px 10px; border-radius:50%; cursor:pointer; font-size:18px; z-index:10001;">›</button>
          
          <!-- File Display Area -->
          <div id="galleryFileDisplay" style="max-width:90%; max-height:80vh; display:flex; align-items:center; justify-content:center;">
            <!-- Content will be loaded here -->
          </div>
        </div>
        
        <!-- File Info and Navigation -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:15px; padding:10px; background:#f8f9fa; border-radius:4px;">
          <div id="fileInfo" style="flex:1;">
            <div id="fileName" style="font-weight:bold; margin-bottom:5px;"></div>
            <div id="fileDate" style="font-size:0.9em; color:#666;"></div>
          </div>
          <div id="fileCounter" style="text-align:center; font-weight:bold; color:#333;"></div>
          <div id="fileType" style="background:#3498db; color:white; padding:4px 8px; border-radius:12px; font-size:0.8em;"></div>
        </div>
      </div>
    </div>
    

    <script>
    function showFileModal(url, type) {
      var modal = document.getElementById('fileModal');
      var body = document.getElementById('fileModalBody');
      if (type === 'pdf') {
        body.innerHTML = '<iframe src="' + url + '" width="800" height="600" style="border:none;"></iframe>';
      } else if (type === 'img') {
        body.innerHTML = '<img src="' + url + '" style="max-width:80vw; max-height:80vh; display:block; margin:auto;" />';
      }
      modal.style.display = 'flex';
    }
    function closeFileModal() {
      var modal = document.getElementById('fileModal');
      var body = document.getElementById('fileModalBody');
      body.innerHTML = '';
      modal.style.display = 'none';
    }
    
    // Gallery modal variables
    var currentFiles = [];
    var currentFileIndex = 0;
    
    function showAllFilesModal(uuid) {
      try {
        // Get the clicked element and its data-files attribute
        var clickedElement = event.target;
        var filesJson = clickedElement.getAttribute('data-files');
        
        currentFiles = JSON.parse(filesJson);
        currentFileIndex = 0;
        
        var modal = document.getElementById('galleryModal');
        var title = document.getElementById('galleryTitle');
        
        title.textContent = 'Project Files (' + currentFiles.length + ' files)';
        modal.style.display = 'flex';
        
        displayCurrentFile();
      } catch (error) {
        console.error('Error parsing files data:', error);
        alert('Error loading files. Please try again.');
      }
    }
    
    function closeGalleryModal() {
      var modal = document.getElementById('galleryModal');
      modal.style.display = 'none';
      currentFiles = [];
      currentFileIndex = 0;
    }
    
    function displayCurrentFile() {
      if (currentFiles.length === 0) return;
      
      var file = currentFiles[currentFileIndex];
      var display = document.getElementById('galleryFileDisplay');
      var fileName = document.getElementById('fileName');
      var fileDate = document.getElementById('fileDate');
      var fileCounter = document.getElementById('fileCounter');
      var fileType = document.getElementById('fileType');
      var prevBtn = document.getElementById('prevBtn');
      var nextBtn = document.getElementById('nextBtn');
      
      // Update file info
      fileName.textContent = file.filename;
      fileDate.textContent = new Date(file.ctime * 1000).toLocaleString();
      fileCounter.textContent = (currentFileIndex + 1) + ' / ' + currentFiles.length;
      fileType.textContent = file.type.toUpperCase();
      
      // Update navigation buttons
      prevBtn.style.display = currentFileIndex > 0 ? 'block' : 'none';
      nextBtn.style.display = currentFileIndex < currentFiles.length - 1 ? 'block' : 'none';
      
      // Generate URL dynamically
      var fileUrl = '/view_file/' + encodeURIComponent(file.rel_path);
      
      // Display file content
      if (file.type === 'pdf') {
        display.innerHTML = '<iframe src="' + fileUrl + '" width="800" height="600" style="border:none; max-width:100%; max-height:100%;"></iframe>';
      } else {
        display.innerHTML = '<img src="' + fileUrl + '" style="max-width:100%; max-height:100%; object-fit:contain;" alt="' + file.filename + '">';
      }
    }
    
    function previousFile() {
      if (currentFileIndex > 0) {
        currentFileIndex--;
        displayCurrentFile();
      }
    }
    
    function nextFile() {
      if (currentFileIndex < currentFiles.length - 1) {
        currentFileIndex++;
        displayCurrentFile();
      }
    }
    
    // Keyboard navigation
    document.addEventListener('keydown', function(event) {
      if (document.getElementById('galleryModal').style.display === 'flex') {
        if (event.key === 'ArrowLeft') {
          previousFile();
        } else if (event.key === 'ArrowRight') {
          nextFile();
        } else if (event.key === 'Escape') {
          closeGalleryModal();
        }
      }
    });
    </script>
    
    <!-- Footer with Logo and Copyright -->
    <div class="header-footer">
        <div class="logo-section">
            <div class="logo">
                <img src="{{ url_for('static', filename='rocket.jpg') }}" alt="Rocket Logo" style="width: 36px; height: 36px; object-fit: contain; border-radius: 50%; background: white;">
            </div>
            <div class="company-info">
                <strong>ARCgis PRO DataBase</strong><br>
                <span style="font-size: 11px;">פרוייקט שימור הידע של (נוסיף שיתאפשר)</span><br>
                <span class="copyright">@Rocket Team Production</span>
            </div>
        </div>

    </div>
</body>
</html>
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
        # This block handles the main search form submission
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
            filters.append(projects_table.c.uuid.ilike(f"{uuid}%"))
        user_name_list = request.form.getlist('user_name')
        selected_user_names = [n for n in user_name_list if n]
        if selected_user_names:
            filters.append(or_(*[projects_table.c.user_name.ilike(f"{n}%") for n in selected_user_names]))
        paper_size = request.form.get('paper_size', '').strip()
        custom_height = request.form.get('custom_height', '').strip()
        custom_width = request.form.get('custom_width', '').strip()
        
        if paper_size:
            if paper_size == 'custom' and custom_height and custom_width:
                try:
                    height_cm = float(custom_height)
                    width_cm = float(custom_width)
                    custom_size_format = f"Custom Size: Height: {height_cm} cm, Width: {width_cm} cm"
                    filters.append(projects_table.c.paper_size.ilike(f"{custom_size_format}%"))
                except ValueError:
                    error = 'Custom height and width must be valid numbers.'
            elif paper_size != 'custom':
                filters.append(projects_table.c.paper_size.ilike(f"{paper_size}%"))
            elif paper_size == 'custom' and (not custom_height or not custom_width):
                error = 'Please enter both height and width for custom size.'
        scale = request.form.get('scale', '').strip()
        if scale:
            try:
                scale_val = float(scale)
                filters.append(projects_table.c.scale == scale_val)
            except ValueError:
                error = 'Scale must be a number.'
        
        # Parse date range
        date_from = request.form.get('date_from', '').strip()
        date_to = request.form.get('date_to', '').strip()
        
        if date_from or date_to:
            # Convert DD/MM/YYYY format to database format (DD-MM-YY) for comparison
            def convert_date_to_db_format(date_str):
                try:
                    if date_str and '/' in date_str:  # DD/MM/YYYY format
                        day, month, year = date_str.split('/')
                        # Convert to DD-MM-YY format for database comparison
                        return f"{day.zfill(2)}-{month.zfill(2)}-{year[2:]}"
                    elif date_str and '-' in date_str:  # DD-MM-YY format (already correct)
                        return date_str
                    return None
                except:
                    return None
            
            if date_from:
                converted_from = convert_date_to_db_format(date_from)
                if converted_from:
                    # For date comparison, we need to ensure proper string comparison
                    filters.append(projects_table.c.date >= converted_from)
                else:
                    error = 'Invalid date format for "From Date". Use DD/MM/YYYY format.'
            
            if date_to:
                converted_to = convert_date_to_db_format(date_to)
                if converted_to:
                    # For date comparison, we need to ensure proper string comparison
                    filters.append(projects_table.c.date <= converted_to)
                else:
                    error = 'Invalid date format for "To Date". Use DD/MM/YYYY format.'

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
            # Add absolute file location for file explorer links
            for proj in results or []:
                rel_path = proj['file_location']
                abs_path = os.path.abspath(rel_path)
                proj['abs_file_location'] = abs_path
                proj['abs_file_location_url'] = abs_path.replace("\\", "/")
                
                # Find all files (PDF, JPEG, PNG) for this project
                file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
                all_files = []
                most_recent = None
                
                for ext, ftype in file_types:
                    pattern = os.path.join(abs_path, f"*.{ext}")
                    files = glob2.glob(pattern)
                    for f in files:
                        ctime = os.path.getctime(f)
                        file_info = {
                            'path': f, 
                            'type': ftype, 
                            'ctime': ctime,
                            'filename': os.path.basename(f),
                            'rel_path': os.path.relpath(f, os.path.abspath('.'))
                        }
                        all_files.append(file_info)
                        
                        # Track the most recent file for the single "View" option
                        if (most_recent is None) or (ctime > most_recent['ctime']):
                            most_recent = file_info
                
                # Sort files by creation time (newest first)
                all_files.sort(key=lambda x: x['ctime'], reverse=True)
                proj['all_files'] = all_files
                proj['file_count'] = len(all_files)
                
                if most_recent:
                    proj['view_file_path'] = most_recent['path']
                    proj['view_file_type'] = most_recent['type']
                else:
                    proj['view_file_path'] = None
                    proj['view_file_type'] = None
    # This block handles GET requests for pagination and table filters
    # For "All Projects" table
    projects_current_page = request.args.get('page', 1, type=int)
    projects_per_page = request.args.get('per_page', 10, type=int)

    projects_filters = {
        'uuid_filter': request.args.get('projects_uuid_filter', '', type=str),
        'project_name_filter': request.args.get('projects_project_name_filter', '', type=str),
        'user_name_filter': request.args.get('projects_user_name_filter', '', type=str),
        'date_filter': request.args.get('projects_date_filter', '', type=str),
        'date_from_filter': request.args.get('projects_date_from_filter', '', type=str),
        'date_to_filter': request.args.get('projects_date_to_filter', '', type=str),
        'file_location_filter': request.args.get('projects_file_location_filter', '', type=str),
        'paper_size_filter': request.args.get('projects_paper_size_filter', '', type=str),
        'scale_filter': request.args.get('projects_scale_filter', '', type=str)
    }

    projects_query_filters = []
    if projects_filters['uuid_filter']:
        projects_query_filters.append(projects_table.c.uuid.ilike(f"{projects_filters['uuid_filter']}%"))
    if projects_filters['project_name_filter']:
        projects_query_filters.append(projects_table.c.project_name.ilike(f"{projects_filters['project_name_filter']}%"))
    if projects_filters['user_name_filter']:
        projects_query_filters.append(projects_table.c.user_name.ilike(f"{projects_filters['user_name_filter']}%"))
    if projects_filters['date_filter']:
        projects_query_filters.append(projects_table.c.date.ilike(f"{projects_filters['date_filter']}%"))
    if projects_filters['file_location_filter']:
        projects_query_filters.append(projects_table.c.file_location.ilike(f"{projects_filters['file_location_filter']}%"))
    if projects_filters['paper_size_filter']:
        projects_query_filters.append(projects_table.c.paper_size.ilike(f"{projects_filters['paper_size_filter']}%"))
    if projects_filters['scale_filter']:
        # Attempt to cast to float for numeric comparison or partial string match
        try:
            scale_val = float(projects_filters['scale_filter'])
            projects_query_filters.append(projects_table.c.scale == scale_val)
        except ValueError:
            # Fallback to string like for non-numeric filter input
            projects_query_filters.append(projects_table.c.scale.cast(text("TEXT")).ilike(f"%{projects_filters['scale_filter']}%"))


    # For "All Areas" table
    areas_current_page = request.args.get('areas_page', 1, type=int)
    areas_per_page = request.args.get('areas_per_page', 10, type=int)

    areas_filters = {
        'id_filter': request.args.get('areas_id_filter', '', type=str),
        'project_id_filter': request.args.get('areas_project_id_filter', '', type=str),
        'xmin_filter': request.args.get('areas_xmin_filter', '', type=str),
        'ymin_filter': request.args.get('areas_ymin_filter', '', type=str),
        'xmax_filter': request.args.get('areas_xmax_filter', '', type=str),
        'ymax_filter': request.args.get('areas_ymax_filter', '', type=str),
    }

    areas_query_filters = []
    if areas_filters['id_filter']:
        try:
            id_val = int(areas_filters['id_filter'])
            areas_query_filters.append(areas_table.c.id == id_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.id.cast(text("TEXT")).ilike(f"%{areas_filters['id_filter']}%"))
    if areas_filters['project_id_filter']:
        areas_query_filters.append(areas_table.c.project_id.ilike(f"%{areas_filters['project_id_filter']}%"))
    if areas_filters['xmin_filter']:
        try:
            xmin_val = float(areas_filters['xmin_filter'])
            areas_query_filters.append(areas_table.c.xmin == xmin_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.xmin.cast(text("TEXT")).ilike(f"%{areas_filters['xmin_filter']}%"))
    if areas_filters['ymin_filter']:
        try:
            ymin_val = float(areas_filters['ymin_filter'])
            areas_query_filters.append(areas_table.c.ymin == ymin_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.ymin.cast(text("TEXT")).ilike(f"%{areas_filters['ymin_filter']}%"))
    if areas_filters['xmax_filter']:
        try:
            xmax_val = float(areas_filters['xmax_filter'])
            areas_query_filters.append(areas_table.c.xmax == xmax_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.xmax.cast(text("TEXT")).ilike(f"%{areas_filters['xmax_filter']}%"))
    if areas_filters['ymax_filter']:
        try:
            ymax_val = float(areas_filters['ymax_filter'])
            areas_query_filters.append(areas_table.c.ymax == ymax_val)
        except ValueError:
            areas_query_filters.append(areas_table.c.ymax.cast(text("TEXT")).ilike(f"%{areas_filters['ymax_filter']}%"))


    with engine.connect() as conn:
        # Get total count for projects pagination
        count_stmt = select(func.count()).select_from(projects_table)
        if projects_query_filters:
            count_stmt = count_stmt.where(and_(*projects_query_filters))
        projects_total_items = conn.execute(count_stmt).scalar_one()

        projects_total_pages = (projects_total_items + projects_per_page - 1) // projects_per_page
        if projects_current_page > projects_total_pages and projects_total_pages > 0:
            projects_current_page = projects_total_pages
        elif projects_total_pages == 0:
             projects_current_page = 1 # No pages if no items

        # Query projects for the current page with filters
        projects_stmt = select(*projects_table.c)
        if projects_query_filters:
            projects_stmt = projects_stmt.where(and_(*projects_query_filters))
        projects_stmt = projects_stmt.limit(projects_per_page).offset((projects_current_page - 1) * projects_per_page)
        projects = conn.execute(projects_stmt).fetchall()
        
        # Add file information for projects (same as in search results)
        projects_list = []
        for proj in projects:
            proj_dict = dict(proj)  # Convert Row to dict
            rel_path = proj_dict['file_location']
            abs_path = os.path.abspath(rel_path)
            proj_dict['abs_file_location'] = abs_path
            proj_dict['abs_file_location_url'] = abs_path.replace("\\", "/")
            
            # Find all files (PDF, JPEG, PNG) for this project
            file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
            all_files = []
            most_recent = None
            
            for ext, ftype in file_types:
                pattern = os.path.join(abs_path, f"*.{ext}")
                files = glob2.glob(pattern)
                for f in files:
                    ctime = os.path.getctime(f)
                    file_info = {
                        'path': f, 
                        'type': ftype, 
                        'ctime': ctime,
                        'filename': os.path.basename(f),
                        'rel_path': os.path.relpath(f, os.path.abspath('.'))
                    }
                    all_files.append(file_info)
                    
                    # Track the most recent file for the single "View" option
                    if (most_recent is None) or (ctime > most_recent['ctime']):
                        most_recent = file_info
            
            # Sort files by creation time (newest first)
            all_files.sort(key=lambda x: x['ctime'], reverse=True)
            proj_dict['all_files'] = all_files
            proj_dict['file_count'] = len(all_files)
            
            if most_recent:
                proj_dict['view_file_path'] = most_recent['path']
                proj_dict['view_file_type'] = most_recent['type']
            else:
                proj_dict['view_file_path'] = None
                proj_dict['view_file_type'] = None
            
            projects_list.append(proj_dict)
        
        projects = projects_list  # Replace the original list with the processed one

        # Get total count for areas pagination
        areas_count_stmt = select(func.count()).select_from(areas_table)
        if areas_query_filters:
            areas_count_stmt = areas_count_stmt.where(and_(*areas_query_filters))
        areas_total_items = conn.execute(areas_count_stmt).scalar_one()

        areas_total_pages = (areas_total_items + areas_per_page - 1) // areas_per_page
        if areas_current_page > areas_total_pages and areas_total_pages > 0:
            areas_current_page = areas_total_pages
        elif areas_total_pages == 0:
            areas_current_page = 1 # No pages if no items

        # Query areas for the current page with filters, joined with projects to get file location
        areas_stmt = select(areas_table.c.id, areas_table.c.project_id, areas_table.c.xmin, areas_table.c.ymin, areas_table.c.xmax, areas_table.c.ymax, projects_table.c.file_location.label('project_file_location'))
        areas_stmt = areas_stmt.select_from(areas_table.join(projects_table, areas_table.c.project_id == projects_table.c.uuid))
        if areas_query_filters:
            areas_stmt = areas_stmt.where(and_(*areas_query_filters))
        areas_stmt = areas_stmt.limit(areas_per_page).offset((areas_current_page - 1) * areas_per_page)
        areas = conn.execute(areas_stmt).fetchall()
        
        # Add file information for areas (show files of associated project)
        areas_list = []
        for area in areas:
            area_dict = dict(area)  # Convert Row to dict
            project_file_location = area_dict['project_file_location']
            abs_path = os.path.abspath(project_file_location)
            area_dict['project_abs_file_location'] = abs_path
            
            # Find all files (PDF, JPEG, PNG) for the associated project
            file_types = [('pdf', 'pdf'), ('jpeg', 'img'), ('jpg', 'img'), ('png', 'img')]
            all_files = []
            most_recent = None
            
            for ext, ftype in file_types:
                pattern = os.path.join(abs_path, f"*.{ext}")
                files = glob2.glob(pattern)
                for f in files:
                    ctime = os.path.getctime(f)
                    file_info = {
                        'path': f, 
                        'type': ftype, 
                        'ctime': ctime,
                        'filename': os.path.basename(f),
                        'rel_path': os.path.relpath(f, os.path.abspath('.'))
                    }
                    all_files.append(file_info)
                    
                    # Track the most recent file for the single "View" option
                    if (most_recent is None) or (ctime > most_recent['ctime']):
                        most_recent = file_info
            
            # Sort files by creation time (newest first)
            all_files.sort(key=lambda x: x['ctime'], reverse=True)
            area_dict['project_all_files'] = all_files
            area_dict['project_file_count'] = len(all_files)
            
            if most_recent:
                area_dict['project_view_file_path'] = most_recent['rel_path']
                area_dict['project_view_file_type'] = most_recent['type']
            else:
                area_dict['project_view_file_path'] = None
                area_dict['project_view_file_type'] = None
            
            areas_list.append(area_dict)
        
        areas = areas_list  # Replace the original list with the processed one


    return render_template_string(
        HTML,
        results=results,
        error=error,
        projects=projects,
        areas=areas,
        user_names=user_names,
        selected_user_names=selected_user_names,
        projects_current_page=projects_current_page,
        projects_per_page=projects_per_page,
        projects_total_pages=projects_total_pages,
        projects_filters=projects_filters,
        areas_current_page=areas_current_page,
        areas_per_page=areas_per_page,
        areas_total_pages=areas_total_pages,
        areas_filters=areas_filters,
        request=request # Pass request object to access form values for sticky inputs
    )

@app.route('/view_file/<path:rel_path>')
def view_file(rel_path):
    import os
    abs_path = os.path.abspath(rel_path)
    # Security: Only allow files inside your project directory
    if not abs_path.startswith(os.path.abspath('.')):
        return "Access denied", 403
    return send_file(abs_path)

@app.route('/delete_project/<uuid>', methods=['POST'])
def delete_project(uuid):
    import shutil
    # Use engine.begin() for a transaction that auto-commits
    with engine.begin() as conn:
        # Get the file location for this project
        sel = select(projects_table.c.file_location).where(projects_table.c.uuid == uuid)
        result = conn.execute(sel).first()
        print(f"[DEBUG] Deletion requested for UUID: {uuid}")
        if result and result[0]:
            folder = result[0]
            print(f"[DEBUG] Project folder to delete: {folder}")
            if os.path.exists(folder) and os.path.isdir(folder):
                try:
                    shutil.rmtree(folder)
                    print(f"[DEBUG] Folder deleted: {folder}")
                except Exception as e:
                    print(f"[DEBUG] Error deleting folder: {e}")
            else:
                print(f"[DEBUG] Folder does not exist or is not a directory: {folder}")
        proj_result = conn.execute(projects_table.delete().where(projects_table.c.uuid == uuid))
        print(f"[DEBUG] Projects deleted: {proj_result.rowcount}")
        area_result = conn.execute(areas_table.delete().where(areas_table.c.project_id == uuid))
        print(f"[DEBUG] Areas deleted: {area_result.rowcount}")
    print(f"[DEBUG] Deletion complete for UUID: {uuid}")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)