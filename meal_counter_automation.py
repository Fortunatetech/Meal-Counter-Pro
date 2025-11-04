#!/usr/bin/env python3
"""
Automated Meal Counter - ULTIMATE FIX
Uses annotation-based text to bypass coordinate issues
"""

import fitz
import re
from collections import defaultdict
from typing import Dict
import sys
import os


class MealCounter:
    
    def __init__(self, input_pdf_path: str, output_pdf_path: str):
        self.input_pdf_path = input_pdf_path
        self.output_pdf_path = output_pdf_path
        
    def categorize_meal(self, meal_name: str) -> str:
        meal_lower = meal_name.lower()
        if 'beef' in meal_lower or 'beefy' in meal_lower:
            return 'Beef Meal'
        elif 'lentil' in meal_lower:
            return 'Lentil Meal'
        elif 'chicken' in meal_lower:
            return 'Chicken Meal'
        elif 'vegetarian' in meal_lower or 'veggie' in meal_lower:
            return 'Vegetarian Meal'
        elif 'fish' in meal_lower:
            return 'Fish Meal'
        else:
            return meal_name.strip()
    
    def extract_meals_from_page(self, page) -> Dict[str, int]:
        text = page.get_text()
        lines = text.split('\n')
        meal_counts = defaultdict(int)
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or line in ['Date', 'School', 'Meal', 'Quantity', 'Grade', 'Class', 'Diner', 'Cycle 5']:
                i += 1
                continue
            
            if re.match(r'\d{2}\s+\w+', line) or re.match(r'\d{4}$', line) or re.match(r'\d{2}/\d{2}/\d{2}', line):
                i += 1
                continue
            
            if 'total' in line.lower():
                i += 1
                continue
            
            if any(keyword in line.lower() for keyword in ['pasta', 'pizza', 'burger', 'salad', 'soup', 'rice', 'chicken', 'beef', 'lentil', 'fish']):
                meal_name = line
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not re.match(r'^\d+$', next_line) and not re.match(r'\d{2}\s+\w+', next_line) and next_line not in ['Date', 'School', 'Meal', 'Quantity', 'Grade', 'Class', 'Diner']:
                        meal_name += ' ' + next_line
                        i += 1
                
                quantity = 0
                for j in range(i + 1, min(i + 5, len(lines))):
                    qty_line = lines[j].strip()
                    if re.match(r'^\d+$', qty_line):
                        qty = int(qty_line)
                        if 1 <= qty <= 100:
                            quantity = qty
                            break
                
                if quantity > 0:
                    meal_category = self.categorize_meal(meal_name)
                    meal_counts[meal_category] += quantity
            
            i += 1
        
        return meal_counts
    
    def add_totals_to_page(self, page, meal_totals: Dict[str, int]):
        """
        Add meal totals using FreeText annotations
        This bypasses coordinate transformation issues
        """
        rect_info = page.rect
        page_width = rect_info.width
        page_height = rect_info.height
        
        sorted_meals = sorted(meal_totals.items())
        
        # Position settings
        line_height = 22
        start_y = page_height - 90 - (len(sorted_meals) * line_height)
        
        for i, (meal_type, total) in enumerate(sorted_meals):
            text = f"{meal_type} Total: {total}"
            
            # Calculate position for this line
            y_top = start_y + (i * line_height)
            y_bottom = y_top + line_height
            
            # Estimate text width
            text_width = len(text) * 9.6  # Approximate for size 16
            x_left = (page_width - text_width) / 2
            x_right = x_left + text_width
            
            # Create rectangle for text
            text_rect = fitz.Rect(x_left, y_top, x_right, y_bottom)
            
            # Add as FreeText annotation (appears as regular text when flattened)
            annot = page.add_freetext_annot(
                text_rect,
                text,
                fontsize=16,
                fontname="helv",
                text_color=(0, 0.7, 0),  # Green
                fill_color=(1, 1, 1),    # White background
                align=fitz.TEXT_ALIGN_CENTER
            )
            
            # Set annotation properties
            annot.set_border(width=0)  # No border
            annot.update()
    
    def process_pdf(self):
        print(f"Opening: {self.input_pdf_path}")
        
        doc = fitz.open(self.input_pdf_path)
        print(f"Pages: {len(doc)}\n")
        
        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]
            meal_totals = self.extract_meals_from_page(page)
            
            if meal_totals:
                print(f"Page {page_num + 1}: {dict(meal_totals)}")
                self.add_totals_to_page(page, meal_totals)
        
        # Save
        print(f"\nSaving: {self.output_pdf_path}")
        doc.save(self.output_pdf_path, incremental=False, encryption=fitz.PDF_ENCRYPT_NONE)
        doc.close()
        
        if os.path.exists(self.output_pdf_path):
            file_size = os.path.getsize(self.output_pdf_path)
            print(f"✓ Done! File size: {file_size:,} bytes")


def main():
    if len(sys.argv) < 2:
        print("Usage: python meal_counter_automation.py <input_pdf> [output_pdf]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_pdf = sys.argv[2]
    else:
        if input_pdf.endswith('.pdf'):
            output_pdf = input_pdf[:-4] + '_with_totals.pdf'
        else:
            output_pdf = input_pdf + '_with_totals.pdf'
    
    print("=" * 60)
    print("MEAL COUNTER - ANNOTATION METHOD")
    print("=" * 60)
    print(f"Input:  {input_pdf}")
    print(f"Output: {output_pdf}")
    print("=" * 60)
    print()
    
    counter = MealCounter(input_pdf, output_pdf)
    counter.process_pdf()


if __name__ == "__main__":
    main()