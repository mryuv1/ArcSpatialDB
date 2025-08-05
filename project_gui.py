"""
Simple GUI for manually adding projects to ArcSpatialDB
Interacts with the Flask API similar to the commit_to_the_db function
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from datetime import datetime
import getpass
import os
import sys
import shutil
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class ProjectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ArcSpatialDB - Add Project Manually")
        self.root.geometry("800x700")
        
        # Load configuration
        self.load_config()
        
        # Areas data list
        self.areas_data = []
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create GUI
        self.create_widgets()
        
        # Pre-fill some default values
        self.prefill_defaults()
    
    def load_config(self):
        """Load configuration from config.py"""
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from config import API_BASE_URL, API_TIMEOUT
            self.api_base_url = API_BASE_URL
            self.api_timeout = API_TIMEOUT
        except ImportError:
            self.api_base_url = "http://localhost:5000"
            self.api_timeout = 30
            print("Warning: Could not load config.py, using defaults")
    
    def create_menu_bar(self):
        """Create the menu bar with File and Help menus"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Clear All Fields", command=self.clear_all_fields)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help)
        help_menu.add_command(label="About", command=self.show_about)
    
    def show_help(self):
        """Display help dialog with usage instructions"""
        help_text = """
ArcSpatialDB Project GUI - User Guide

This application allows you to manually add projects to your ArcSpatialDB database.

=== PROJECT INFORMATION ===

• Project Name: Enter a descriptive name for your project (Required)
• Description: Optional description of the project
• User Name: Automatically filled with current user, can be modified (Required)
• Date: Automatically filled with current date in DD-MM-YY format (Required)
• Project Image: Select an image file (PNG/JPEG/PDF) representing the project (Required)
• Project File: Select the project file (.aprx/.blaze_proj) - Optional
• Output Folder: Select destination folder where files will be copied/moved (Required)
• File Operation: Choose whether to Copy or Move files (default: Move)
• Paper Size: Select from dropdown (A0-A5, B0 in Portrait/Landscape) (Required)

=== FILE OPERATIONS ===

After successfully adding the project to the database:
• Files will be automatically copied or moved to the Output Folder
• Project Image and Project File will be renamed to match the Project Name
• Original file extensions will be preserved
• Move operation removes files from original location
• Copy operation keeps files in both locations

=== MAP AREAS ===

You can add multiple map areas for each project (at least one is required):

• X Min/Max: Minimum and maximum X coordinates (in UTM or appropriate projection)
• Y Min/Max: Minimum and maximum Y coordinates (in UTM or appropriate projection)
• Scale: Enter scale information (e.g., "Scale: 1:1000")

Steps to add areas:
1. Fill in the coordinate fields
2. Click "Add Area" to add to the list
3. Repeat for multiple areas
4. Use "Remove Selected Area" to delete areas from the list
5. Use "Clear" to clear input fields for next area

=== SUBMITTING PROJECTS ===

1. Fill in all required project information
2. Select project image file (required)
3. Optionally select project file
4. Choose output folder and file operation
5. Add at least one map area (REQUIRED)
6. Click "Add Project to Database"
7. Files will be processed automatically after database entry
8. You'll receive confirmation with the generated UUID
9. Option to clear fields for entering another project

=== TIPS ===

• Project Image accepts: PNG, JPEG, PDF files
• Project File accepts: .aprx (ArcGIS), .blaze_proj files
• All coordinate values should be numeric
• Date format must be DD-MM-YY (e.g., 05-08-25)
• Scale field is flexible - you can enter just numbers or descriptive text
• The Flask server must be running for database submission to work
• Files are renamed automatically using the Project Name

=== TROUBLESHOOTING ===

• "Connection failed" → Ensure Flask server is running at the configured URL
• "Invalid coordinate format" → Check that coordinates are numeric
• "Date format error" → Use DD-MM-YY format
• "Missing fields" → Fill in all required fields marked as (Required)
• "File operation failed" → Check file permissions and disk space
• "Invalid file format" → Ensure files match required extensions

For technical support, check the server logs or contact your system administrator.
"""
        
        # Create help window
        help_window = tk.Toplevel(self.root)
        help_window.title("ArcSpatialDB GUI - Help")
        help_window.geometry("800x600")
        help_window.resizable(True, True)
        
        # Center the help window
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Create text widget with scrollbar
        frame = ttk.Frame(help_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text widget
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 10), bg="white", fg="black")
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Insert help text
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        close_frame = ttk.Frame(help_window)
        close_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(close_frame, text="Close", command=help_window.destroy).pack(side=tk.RIGHT)
        
        # Focus on help window
        help_window.focus_set()
    
    def show_about(self):
        """Display about dialog"""
        about_text = """ArcSpatialDB Project GUI
Version 1.0

A standalone GUI application for manually adding projects to the ArcSpatialDB database.

Features:
• Manual project entry with validation
• Multiple map areas per project
• Direct API integration with Flask server
• User-friendly interface with error handling

Built with Python tkinter
Part of the ArcSpatialDB system

© 2025 Rocket Team Production"""
        
        messagebox.showinfo("About ArcSpatialDB GUI", about_text)
    
    def toggle_uuid_placement(self):
        """Enable/disable UUID placement options based on checkbox"""
        if self.add_uuid_var.get():
            # Enable UUID placement options
            for child in self.uuid_placement_frame.winfo_children():
                for grandchild in child.winfo_children():
                    grandchild.configure(state="normal")
        else:
            # Disable UUID placement options
            for child in self.uuid_placement_frame.winfo_children():
                for grandchild in child.winfo_children():
                    grandchild.configure(state="disabled")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Project Information Section
        project_frame = ttk.LabelFrame(main_frame, text="Project Information", padding=10)
        project_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Project Name
        ttk.Label(project_frame, text="Project Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.project_name_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.project_name_var, width=50).grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # Description
        ttk.Label(project_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.description_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.description_var, width=50).grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # User Name
        ttk.Label(project_frame, text="User Name:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.user_name_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.user_name_var, width=50).grid(row=2, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # Date
        ttk.Label(project_frame, text="Date (DD-MM-YY):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.date_var = tk.StringVar()
        ttk.Entry(project_frame, textvariable=self.date_var, width=50).grid(row=3, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # Project Image (Required)
        ttk.Label(project_frame, text="Project Image (PNG/JPEG/PDF):").grid(row=4, column=0, sticky=tk.W, pady=2)
        image_frame = ttk.Frame(project_frame)
        image_frame.grid(row=4, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.project_image_var = tk.StringVar()
        ttk.Entry(image_frame, textvariable=self.project_image_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(image_frame, text="Browse", command=self.browse_project_image).pack(side=tk.RIGHT, padx=(5, 0))

        # Project File (Optional)
        ttk.Label(project_frame, text="Project File (.aprx/.blaze_proj):").grid(row=5, column=0, sticky=tk.W, pady=2)
        project_frame2 = ttk.Frame(project_frame)
        project_frame2.grid(row=5, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.project_file_var = tk.StringVar()
        ttk.Entry(project_frame2, textvariable=self.project_file_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(project_frame2, text="Browse", command=self.browse_project_file).pack(side=tk.RIGHT, padx=(5, 0))

        # Output Location (Required)
        ttk.Label(project_frame, text="Output Folder:").grid(row=6, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(project_frame)
        output_frame.grid(row=6, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.output_location_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_location_var, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse", command=self.browse_output_folder).pack(side=tk.RIGHT, padx=(5, 0))

        # Copy/Move Option
        ttk.Label(project_frame, text="File Operation:").grid(row=7, column=0, sticky=tk.W, pady=2)
        operation_frame = ttk.Frame(project_frame)
        operation_frame.grid(row=7, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.file_operation_var = tk.StringVar(value="move")
        ttk.Radiobutton(operation_frame, text="Move Files", variable=self.file_operation_var, value="move").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(operation_frame, text="Copy Files", variable=self.file_operation_var, value="copy").pack(side=tk.LEFT)

        # UUID Placement Option
        ttk.Label(project_frame, text="UUID Placement on Image:").grid(row=8, column=0, sticky=tk.W, pady=2)
        uuid_frame = ttk.Frame(project_frame)
        uuid_frame.grid(row=8, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # Add UUID checkbox
        uuid_checkbox_frame = ttk.Frame(uuid_frame)
        uuid_checkbox_frame.pack(fill=tk.X, pady=(0, 5))
        self.add_uuid_var = tk.BooleanVar(value=True)  # Default to True
        ttk.Checkbutton(uuid_checkbox_frame, text="Add UUID overlay to image/PDF", 
                       variable=self.add_uuid_var, command=self.toggle_uuid_placement).pack(side=tk.LEFT)
        
        # UUID placement options frame
        self.uuid_placement_frame = ttk.Frame(uuid_frame)
        self.uuid_placement_frame.pack(fill=tk.X)
        self.uuid_placement_var = tk.StringVar(value="bottom_right")
        
        # Create placement options in a more compact layout
        placement_row1 = ttk.Frame(self.uuid_placement_frame)
        placement_row1.pack(fill=tk.X, pady=(0, 2))
        ttk.Radiobutton(placement_row1, text="Top Left", variable=self.uuid_placement_var, value="top_left").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(placement_row1, text="Top Right", variable=self.uuid_placement_var, value="top_right").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(placement_row1, text="Middle Left", variable=self.uuid_placement_var, value="middle_left").pack(side=tk.LEFT)
        
        placement_row2 = ttk.Frame(self.uuid_placement_frame)
        placement_row2.pack(fill=tk.X)
        ttk.Radiobutton(placement_row2, text="Middle Right", variable=self.uuid_placement_var, value="middle_right").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(placement_row2, text="Bottom Left", variable=self.uuid_placement_var, value="bottom_left").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(placement_row2, text="Bottom Right", variable=self.uuid_placement_var, value="bottom_right").pack(side=tk.LEFT)

        # Paper Size
        ttk.Label(project_frame, text="Paper Size:").grid(row=9, column=0, sticky=tk.W, pady=2)
        self.paper_size_var = tk.StringVar()
        paper_combo = ttk.Combobox(project_frame, textvariable=self.paper_size_var, 
                                  values=["A0 (Portrait)", "A0 (Landscape)", "A1 (Portrait)", "A1 (Landscape)", 
                                         "A2 (Portrait)", "A2 (Landscape)", "A3 (Portrait)", "A3 (Landscape)",
                                         "A4 (Portrait)", "A4 (Landscape)", "A5 (Portrait)", "A5 (Landscape)",
                                         "B0 (Portrait)", "B0 (Landscape)"], width=47)
        paper_combo.grid(row=9, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # Configure column weights
        project_frame.columnconfigure(1, weight=1)
        image_frame.columnconfigure(0, weight=1)
        project_frame2.columnconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        
        # Areas Section
        areas_frame = ttk.LabelFrame(main_frame, text="Map Areas", padding=10)
        areas_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create horizontal layout: input fields on left, listbox on right
        areas_container = ttk.Frame(areas_frame)
        areas_container.pack(fill=tk.BOTH, expand=True)
        
        # Left side: Areas input section
        input_frame = ttk.Frame(areas_container)
        input_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Area input fields in a grid
        ttk.Label(input_frame, text="X Min:").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.xmin_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.xmin_var, width=12).grid(row=0, column=1, padx=2, pady=2)
        
        ttk.Label(input_frame, text="Y Min:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.ymin_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.ymin_var, width=12).grid(row=1, column=1, padx=2, pady=2)
        
        ttk.Label(input_frame, text="X Max:").grid(row=2, column=0, padx=2, pady=2, sticky=tk.W)
        self.xmax_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.xmax_var, width=12).grid(row=2, column=1, padx=2, pady=2)
        
        ttk.Label(input_frame, text="Y Max:").grid(row=3, column=0, padx=2, pady=2, sticky=tk.W)
        self.ymax_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.ymax_var, width=12).grid(row=3, column=1, padx=2, pady=2)
        
        ttk.Label(input_frame, text="Scale:").grid(row=4, column=0, padx=2, pady=2, sticky=tk.W)
        self.scale_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.scale_var, width=25).grid(row=4, column=1, columnspan=2, padx=2, pady=2, sticky=tk.EW)
        
        # Buttons for area management
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=5, column=0, columnspan=2, padx=2, pady=10, sticky=tk.EW)
        ttk.Button(button_frame, text="Add Area", command=self.add_area).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Clear", command=self.clear_area_fields).pack(side=tk.LEFT)
        
        # Right side: Areas listbox
        listbox_frame = ttk.Frame(areas_container)
        listbox_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(listbox_frame, text="Added Areas:").pack(anchor=tk.W)
        
        # Listbox with scrollbar
        list_container = ttk.Frame(listbox_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.areas_listbox = tk.Listbox(list_container, yscrollcommand=scrollbar.set, height=8)
        self.areas_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.areas_listbox.yview)
        
        # Remove area button
        ttk.Button(listbox_frame, text="Remove Selected Area", command=self.remove_area).pack(pady=5)
        
        # Submit and Status Section
        submit_frame = ttk.Frame(main_frame)
        submit_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Submit button
        ttk.Button(submit_frame, text="Add Project to Database", command=self.submit_project, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear all button
        ttk.Button(submit_frame, text="Clear All Fields", command=self.clear_all_fields).pack(side=tk.LEFT)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to add project...")
        ttk.Label(main_frame, textvariable=self.status_var, foreground="blue").pack(anchor=tk.W)
    
    def prefill_defaults(self):
        """Pre-fill some default values"""
        # Set current user
        try:
            self.user_name_var.set(getpass.getuser())
        except:
            self.user_name_var.set("")
        
        # Set current date
        current_date = datetime.now().strftime("%d-%m-%y")
        self.date_var.set(current_date)
        
        # Set default paper size
        self.paper_size_var.set("A4 (Portrait)")
        
        # Set default scale format
        self.scale_var.set("1:1000")
    
    def browse_project_image(self):
        """Open file browser dialog for project image"""
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.pdf"),
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PDF files", "*.pdf"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(
            title="Select Project Image",
            filetypes=file_types
        )
        if file_path:
            self.project_image_var.set(file_path)
    
    def browse_project_file(self):
        """Open file browser dialog for project file"""
        file_types = [
            ("Project files", "*.aprx *.blaze_proj"),
            ("ArcGIS Project", "*.aprx"),
            ("Blaze Project", "*.blaze_proj"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(
            title="Select Project File",
            filetypes=file_types
        )
        if file_path:
            self.project_file_var.set(file_path)
    
    def browse_output_folder(self):
        """Open folder browser dialog for output location"""
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_location_var.set(folder)
    
    def add_area(self):
        """Add area to the areas list"""
        try:
            # Validate input
            xmin_str = self.xmin_var.get().strip()
            ymin_str = self.ymin_var.get().strip()
            xmax_str = self.xmax_var.get().strip()
            ymax_str = self.ymax_var.get().strip()
            scale = self.scale_var.get().strip()
            
            # Check if coordinate fields are empty
            if not xmin_str or not ymin_str or not xmax_str or not ymax_str:
                messagebox.showerror("Error", "All coordinate fields (X Min, Y Min, X Max, Y Max) are required")
                return
            
            # Convert to numbers and validate
            try:
                xmin = float(xmin_str)
                ymin = float(ymin_str)
                xmax = float(xmax_str)
                ymax = float(ymax_str)
            except ValueError:
                messagebox.showerror("Error", "All coordinate values must be valid numbers (integers or decimals)")
                return
            
            # Validate min/max relationships
            if xmin >= xmax:
                messagebox.showerror("Error", "X Min must be less than X Max")
                return
            
            if ymin >= ymax:
                messagebox.showerror("Error", "Y Min must be less than Y Max")
                return
            
            if not scale:
                messagebox.showerror("Error", "Scale cannot be empty")
                return
            
            # Process scale to enforce 1:number format
            scale_processed = scale.strip()
            # Enforce 1:number format
            if scale_processed.startswith("1:"):
                # Already in correct format, validate the number part
                number_part = scale_processed[2:].strip()
                try:
                    float(number_part)  # Validate it's a number
                except ValueError:
                    messagebox.showerror("Error", "Scale must be in format '1:number' (e.g., '1:1000')")
                    return
            else:
                # Try to convert to 1:number format
                try:
                    # Check if it's a valid number
                    float(scale_processed)
                    scale_processed = f"1:{scale_processed}"
                except ValueError:
                    messagebox.showerror("Error", "Scale must be in format '1:number' (e.g., '1:1000')")
                    return
            
            # Create area data
            area_data = {
                'xmin': int(xmin),
                'ymin': int(ymin),
                'xmax': int(xmax),
                'ymax': int(ymax),
                'scale': scale_processed
            }
            
            # Add to list
            self.areas_data.append(area_data)
            
            # Update listbox
            area_text = f"X: {int(xmin)}-{int(xmax)}, Y: {int(ymin)}-{int(ymax)}, {scale_processed}"
            self.areas_listbox.insert(tk.END, area_text)
            
            # Clear input fields
            self.clear_area_fields()
            
            self.status_var.set(f"Added area {len(self.areas_data)}. Ready to add more areas or submit project.")
            
        except ValueError as e:
            messagebox.showerror("Error", "Please enter valid numeric values for coordinates")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding area: {str(e)}")
    
    def remove_area(self):
        """Remove selected area from the list"""
        selection = self.areas_listbox.curselection()
        if selection:
            index = selection[0]
            self.areas_listbox.delete(index)
            del self.areas_data[index]
            self.status_var.set(f"Removed area. {len(self.areas_data)} areas remaining.")
        else:
            messagebox.showwarning("Warning", "Please select an area to remove")
    
    def clear_area_fields(self):
        """Clear area input fields"""
        self.xmin_var.set("")
        self.ymin_var.set("")
        self.xmax_var.set("")
        self.ymax_var.set("")
        # Don't clear scale as it's often the same for multiple areas
    
    def clear_all_fields(self):
        """Clear all fields and reset to defaults"""
        self.project_name_var.set("")
        self.description_var.set("")
        self.project_image_var.set("")
        self.project_file_var.set("")
        self.output_location_var.set("")
        self.clear_area_fields()
        self.areas_data.clear()
        self.areas_listbox.delete(0, tk.END)
        self.prefill_defaults()
        self.status_var.set("All fields cleared. Ready to add new project.")
    
    def validate_inputs(self):
        """Validate all required inputs"""
        if not self.project_name_var.get().strip():
            messagebox.showerror("Error", "Project Name is required")
            return False
        
        if not self.user_name_var.get().strip():
            messagebox.showerror("Error", "User Name is required")
            return False
        
        if not self.date_var.get().strip():
            messagebox.showerror("Error", "Date is required")
            return False
        
        if not self.project_image_var.get().strip():
            messagebox.showerror("Error", "Project Image is required")
            return False
        
        if not self.output_location_var.get().strip():
            messagebox.showerror("Error", "Output Folder is required")
            return False
        
        if not self.paper_size_var.get().strip():
            messagebox.showerror("Error", "Paper Size is required")
            return False
        
        # Validate that at least one map area is added
        if len(self.areas_data) == 0:
            messagebox.showerror("Error", "At least one Map Area is required")
            return False
        
        # Validate date format
        try:
            datetime.strptime(self.date_var.get().strip(), "%d-%m-%y")
        except ValueError:
            messagebox.showerror("Error", "Date must be in DD-MM-YY format")
            return False
        
        # Validate project image file format
        image_path = self.project_image_var.get().strip()
        if image_path:
            valid_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
            if not any(image_path.lower().endswith(ext) for ext in valid_extensions):
                messagebox.showerror("Error", "Project Image must be PNG, JPEG, or PDF format")
                return False
        
        # Validate project file format (if provided)
        project_file = self.project_file_var.get().strip()
        if project_file:
            valid_project_extensions = ['.aprx', '.blaze_proj']
            if not any(project_file.lower().endswith(ext) for ext in valid_project_extensions):
                messagebox.showerror("Error", "Project File must be .aprx or .blaze_proj format")
                return False
        
        return True
    
    def submit_project(self):
        """Submit project to the API"""
        if not self.validate_inputs():
            return
        
        # Prepare payload
        payload = {
            "project_name": self.project_name_var.get().strip(),
            "user_name": self.user_name_var.get().strip(),
            "date": self.date_var.get().strip(),
            "file_location": self.output_location_var.get().strip(),  # Using output location for API compatibility
            "paper_size": self.paper_size_var.get().strip(),
            "description": self.description_var.get().strip(),
            "areas": self.areas_data,
            "project_image": self.project_image_var.get().strip(),
            "project_file": self.project_file_var.get().strip(),
            "output_location": self.output_location_var.get().strip()
        }
        
        try:
            self.status_var.set("Submitting project to database...")
            self.root.update()
            
            # Send request to API
            api_url = f"{self.api_base_url}/api/add_project"
            response = requests.post(api_url, json=payload, timeout=self.api_timeout)
            
            if response.status_code == 201:
                response_data = response.json()
                generated_uuid = response_data.get('uuid')
                
                # Now handle file operations
                try:
                    self.status_var.set("Processing files...")
                    self.root.update()
                    
                    success = self.handle_file_operations(generated_uuid)
                    
                    if success:
                        messagebox.showinfo("Success", 
                            f"✅ Project added successfully!\n\n"
                            f"Generated UUID: {generated_uuid}\n"
                            f"Project Name: {payload['project_name']}\n"
                            f"Areas Added: {len(self.areas_data)}\n"
                            f"Files processed successfully!")
                        
                        self.status_var.set(f"✅ Project added successfully! UUID: {generated_uuid}")
                    else:
                        messagebox.showwarning("Partial Success", 
                            f"⚠️ Project added to database but file operations had issues\n\n"
                            f"Generated UUID: {generated_uuid}\n"
                            f"Check the status bar for details.")
                
                except Exception as file_error:
                    messagebox.showwarning("Partial Success", 
                        f"⚠️ Project added to database but file operations failed\n\n"
                        f"Generated UUID: {generated_uuid}\n"
                        f"File Error: {str(file_error)}")
                    self.status_var.set(f"⚠️ Project added, file operations failed: {str(file_error)}")
                
                # Ask if user wants to clear fields for next entry
                if messagebox.askyesno("Clear Fields", "Would you like to clear all fields to add another project?"):
                    self.clear_all_fields()
                
            else:
                error_msg = response.json().get('error', 'Unknown error')
                messagebox.showerror("API Error", 
                    f"❌ Failed to add project\n\n"
                    f"Status Code: {response.status_code}\n"
                    f"Error: {error_msg}")
                self.status_var.set(f"❌ Error: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", 
                f"❌ Failed to connect to database server\n\n"
                f"Error: {str(e)}\n\n"
                f"Please ensure the Flask server is running at {self.api_base_url}")
            self.status_var.set("❌ Connection failed. Check if server is running.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.status_var.set(f"❌ Unexpected error: {str(e)}")
    
    def handle_file_operations(self, project_uuid):
        """Handle copying/moving files to output location with renamed files"""
        try:
            output_dir = self.output_location_var.get().strip()
            project_name = self.project_name_var.get().strip()
            operation = self.file_operation_var.get()
            
            # Create project-specific folder inside output directory
            project_folder = os.path.join(output_dir, project_name)
            if not os.path.exists(project_folder):
                os.makedirs(project_folder)
            
            success = True
            processed_files = []
            
            # Process project image (required)
            image_path = self.project_image_var.get().strip()
            if image_path and os.path.exists(image_path):
                # Get file extension
                _, ext = os.path.splitext(image_path)
                new_image_name = f"{project_name}{ext}"
                dest_image_path = os.path.join(project_folder, new_image_name)
                
                try:
                    if operation == "copy":
                        shutil.copy2(image_path, dest_image_path)
                    else:  # move
                        shutil.move(image_path, dest_image_path)
                    
                    # Add UUID overlay to the image/PDF if enabled
                    if self.add_uuid_var.get():
                        uuid_text = f"Export ID: {project_uuid}"
                        placement = self.uuid_placement_var.get()
                        
                        if ext.lower() == '.pdf':
                            uuid_success = self.add_uuid_to_pdf(dest_image_path, uuid_text, placement)
                        else:  # For image files (PNG, JPG, JPEG)
                            uuid_success = self.add_uuid_to_image(dest_image_path, uuid_text, placement)
                        
                        if uuid_success:
                            processed_files.append(f"Image: {new_image_name} (with UUID)")
                        else:
                            processed_files.append(f"Image: {new_image_name} (UUID overlay failed)")
                    else:
                        processed_files.append(f"Image: {new_image_name}")
                        
                except Exception as e:
                    self.status_var.set(f"❌ Failed to {operation} image file: {str(e)}")
                    success = False
            
            # Process project file (optional)
            project_file_path = self.project_file_var.get().strip()
            if project_file_path and os.path.exists(project_file_path):
                # Get file extension
                _, ext = os.path.splitext(project_file_path)
                new_project_name = f"{project_name}{ext}"
                dest_project_path = os.path.join(project_folder, new_project_name)
                
                try:
                    if operation == "copy":
                        shutil.copy2(project_file_path, dest_project_path)
                    else:  # move
                        shutil.move(project_file_path, dest_project_path)
                    processed_files.append(f"Project: {new_project_name}")
                except Exception as e:
                    self.status_var.set(f"❌ Failed to {operation} project file: {str(e)}")
                    success = False
            
            # Update status with processed files
            if processed_files:
                files_str = ", ".join(processed_files)
                operation_past = "copied" if operation == "copy" else "moved"
                self.status_var.set(f"✅ Files {operation_past} to folder '{project_name}': {files_str}")
            
            return success
            
        except Exception as e:
            self.status_var.set(f"❌ File operation error: {str(e)}")
            return False
    
    def add_uuid_to_image(self, image_path, uuid_text, placement):
        """Add UUID text overlay to an image"""
        if not PIL_AVAILABLE:
            print("Warning: PIL not available, skipping UUID overlay on image")
            return False
        
        try:
            # Open the image
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            
            # Try to use a system font, fallback to default
            try:
                # Try different font sizes based on image size
                font_size = max(20, min(image.width, image.height) // 50)
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    # If all else fails, use basic drawing
                    font = None
            
            # Get text dimensions
            if font:
                bbox = draw.textbbox((0, 0), uuid_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # Estimate text size for default font
                text_width = len(uuid_text) * 8
                text_height = 15
            
            # Calculate position based on placement choice
            margin = 20
            positions = {
                'top_left': (margin, margin),
                'top_right': (image.width - text_width - margin, margin),
                'middle_left': (margin, (image.height - text_height) // 2),
                'middle_right': (image.width - text_width - margin, (image.height - text_height) // 2),
                'bottom_left': (margin, image.height - text_height - margin),
                'bottom_right': (image.width - text_width - margin, image.height - text_height - margin)
            }
            
            position = positions.get(placement, positions['bottom_right'])
            
            # Draw background rectangle for better visibility
            bg_margin = 5
            bg_box = [
                position[0] - bg_margin,
                position[1] - bg_margin,
                position[0] + text_width + bg_margin,
                position[1] + text_height + bg_margin
            ]
            draw.rectangle(bg_box, fill=(255, 255, 255, 200), outline=(0, 0, 0))
            
            # Draw the text
            if font:
                draw.text(position, uuid_text, fill=(0, 0, 0), font=font)
            else:
                draw.text(position, uuid_text, fill=(0, 0, 0))
            
            # Save the modified image
            image.save(image_path)
            return True
            
        except Exception as e:
            print(f"Error adding UUID to image: {str(e)}")
            return False
    
    def add_uuid_to_pdf(self, pdf_path, uuid_text, placement):
        """Add UUID text overlay to a PDF using PyMuPDF"""
        if not PYMUPDF_AVAILABLE:
            print("Warning: PyMuPDF not available, skipping UUID overlay on PDF")
            return False
        
        try:
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            # Loop through all pages in the PDF
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_rect = page.rect
                
                # Calculate position based on placement choice
                margin = 20
                font_size = 12
                
                # Estimate text dimensions (PyMuPDF will calculate exact dimensions)
                text_rect = fitz.Rect(0, 0, 200, 20)  # Approximate size
                
                positions = {
                    'top_left': fitz.Point(margin, margin + font_size),
                    'top_right': fitz.Point(page_rect.width - 200 - margin, margin + font_size),
                    'middle_left': fitz.Point(margin, page_rect.height / 2),
                    'middle_right': fitz.Point(page_rect.width - 200 - margin, page_rect.height / 2),
                    'bottom_left': fitz.Point(margin, page_rect.height - margin),
                    'bottom_right': fitz.Point(page_rect.width - 200 - margin, page_rect.height - margin)
                }
                
                position = positions.get(placement, positions['bottom_right'])
                
                # Create a text rectangle at the specified position
                text_rect = fitz.Rect(position.x, position.y - font_size, 
                                    position.x + 200, position.y + 5)
                
                # Add background rectangle for better visibility
                bg_rect = fitz.Rect(text_rect.x0 - 5, text_rect.y0 - 5, 
                                  text_rect.x1 + 5, text_rect.y1 + 5)
                page.draw_rect(bg_rect, color=(1, 1, 1), fill=(1, 1, 1), width=1)  # White background
                page.draw_rect(bg_rect, color=(0, 0, 0), width=1)  # Black border
                
                # Insert the text
                page.insert_text(position, uuid_text, fontsize=font_size, 
                               color=(0, 0, 0))  # Black text
            
            # Save the modified PDF
            doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()
            
            return True
            
        except Exception as e:
            print(f"Error adding UUID to PDF: {str(e)}")
            return False


def main():
    """Main function to run the GUI"""
    try:
        # Create the main window
        root = tk.Tk()
        
        # Configure style for modern look
        style = ttk.Style()
        style.theme_use('clam')  # Modern theme
        
        # Create and run the application
        app = ProjectGUI(root)
        
        # Center the window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        # Start the GUI
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
