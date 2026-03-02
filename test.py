import flet as ft

def main(page: ft.Page):
    print("Checking page methods for file selection...")
    
    # Look for any file/pick related methods on page
    file_methods = [method for method in dir(page) if 'file' in method.lower() or 'pick' in method.lower() or 'dialog' in method.lower()]
    print(f"File/pick/dialog related methods on page: {file_methods}")
    
    # Check if there's a direct method to pick files
    if hasattr(page, 'pick_files'):
        print("page.pick_files exists!")
    
    if hasattr(page, 'open_file_picker'):
        print("page.open_file_picker exists!")
        
    # Also check what dialog types exist
    dialog_attrs = [attr for attr in dir(ft) if 'dialog' in attr.lower() or 'picker' in attr.lower()]
    print(f"\nDialog/Picker controls in ft: {dialog_attrs}")
    
    page.add(ft.Text("Check terminal for output"))

if __name__ == "__main__":
    ft.run(main)