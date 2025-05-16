with open('search_gui_pyside.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    with open('indentation_check.txt', 'w', encoding='utf-8') as out_f:
        # Find the _show_pro_feature_dialog_message method
        for i, line in enumerate(lines):
            if '_show_pro_feature_dialog_message' in line:
                start_index = i
                out_f.write(f"Found method at line {i+1}: {repr(line)}\n")
                break
        
        # Output the method and some lines after it
        for i, line in enumerate(lines[start_index:start_index+20], start_index):
            out_f.write(f"{i+1}: {repr(line)}\n")
            
print("Indentation check complete. Results in indentation_check.txt") 