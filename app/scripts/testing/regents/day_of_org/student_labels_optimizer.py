import pandas as pd
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass


@dataclass
class ProcessedSublist:
    original_index: int
    data: List[Dict]
    size: int
    category: str  # 'small', 'medium', 'large', 'oversized'


class SmallFirstLabelOrganizer:
    """
    Label optimizer that prioritizes efficient packing:
    1. Reorders sublists: small (<10) first, then medium (10-20), then large (21+)
    2. Small sublists are packed by columns to maximize efficiency
    3. Medium sublists are packed by rows
    4. Large sublists get dedicated processing
    5. Prevents small sublists from wasting entire sheets
    """

    def __init__(self, rows: int = 10, cols: int = 3):
        self.rows = rows
        self.cols = cols
        self.labels_per_sheet = rows * cols  # 30

    def organize_labels(self, sublists: List[List[Dict]]) -> List[Dict]:
        """
        Main method that reorders and optimally packs sublists.
        """
        # Step 1: Categorize and sort sublists by size
        processed_sublists = self._categorize_and_sort_sublists(sublists)

        if not processed_sublists:
            return []

        # Step 2: Pack sublists using small-first strategy
        sheets = self._pack_with_small_first_strategy(processed_sublists)

        # Step 3: Convert all sheets to row order
        return self._convert_sheets_to_row_order(sheets)

    def _categorize_and_sort_sublists(
        self, sublists: List[List[Dict]]
    ) -> List[ProcessedSublist]:
        """
        Categorize sublists by size and sort them for optimal packing.
        """
        processed = []

        for i, sublist in enumerate(sublists):
            if not sublist:  # Skip empty sublists
                continue

            size = len(sublist)
            if size < 10:
                category = "small"
            elif size <= 20:
                category = "medium"
            elif size <= self.labels_per_sheet:
                category = "large"
            else:
                category = "oversized"

            processed.append(ProcessedSublist(i, sublist, size, category))

        # Sort by category priority: small first, then medium, then large, then oversized
        category_priority = {"small": 1, "medium": 2, "large": 3, "oversized": 4}
        processed.sort(key=lambda x: (category_priority[x.category], x.size))

        return processed

    def _pack_with_small_first_strategy(
        self, processed_sublists: List[ProcessedSublist]
    ) -> List[Dict]:
        """
        Pack sublists using small-first strategy with overflow capability.
        """
        sheets = []
        i = 0

        while i < len(processed_sublists):
            current = processed_sublists[i]

            if current.category == "oversized":
                # Handle oversized sublists (>30 labels)
                sheet_data, next_i = self._handle_oversized_sublist(
                    processed_sublists, i
                )
                sheets.extend(sheet_data)
                i = next_i
            elif current.category == "small":
                # Pack small sublists together by columns
                sheet_data, next_i = self._pack_small_sublists(processed_sublists, i)
                sheets.append(sheet_data)
                i = next_i
            else:
                # Pack medium/large sublists with overflow capability
                sheet_configs, next_i = self._pack_medium_large_sublists(
                    processed_sublists, i
                )
                sheets.extend(sheet_configs)
                i = next_i

        return sheets

    def _pack_small_sublists(
        self, processed_sublists: List[ProcessedSublist], start_idx: int
    ) -> Tuple[Dict, int]:
        """
        Pack small sublists by columns, with each sublist taking a full column.
        Adds padding to fill complete columns and ensures clean cutting lines.
        """
        sheet_data = []
        columns_used = 0
        sublists_packed = []
        i = start_idx

        # Pack sublists column by column
        while i < len(processed_sublists) and columns_used < self.cols:
            current = processed_sublists[i]

            # Stop if we hit a non-small sublist
            if current.category != "small":
                break

            # Add the sublist data
            column_data = list(current.data)

            # Pad to fill the complete column (10 rows)
            while len(column_data) < self.rows:
                column_data.append({})

            # Add this column's data to sheet_data
            sheet_data.extend(column_data)
            sublists_packed.append(current)
            columns_used += 1
            i += 1

        # If we didn't pack any small sublists, pack at least one
        if not sublists_packed and start_idx < len(processed_sublists):
            current = processed_sublists[start_idx]
            column_data = list(current.data)

            # Pad to fill the complete column
            while len(column_data) < self.rows:
                column_data.append({})

            sheet_data.extend(column_data)
            sublists_packed.append(current)
            columns_used += 1
            i = start_idx + 1

        # Fill remaining columns with empty labels
        while columns_used < self.cols:
            for _ in range(self.rows):
                sheet_data.append({})
            columns_used += 1

        total_labels = sum(sl.size for sl in sublists_packed)

        return {
            "data": sheet_data,
            "format": "column",  # Small sublists use column packing
            "sublists_info": [(sl.original_index, sl.size) for sl in sublists_packed],
            "efficiency": total_labels / self.labels_per_sheet,
            "columns_used": len(sublists_packed),
        }, i

    def _pack_medium_large_sublists(
        self, processed_sublists: List[ProcessedSublist], start_idx: int
    ) -> Tuple[List[Dict], int]:
        """
        Pack medium and large sublists with overflow capability.
        Large sublists can span multiple sheets, using leftover space efficiently.
        """
        sheets = []
        current_sheet_data = []
        i = start_idx

        while i < len(processed_sublists):
            current = processed_sublists[i]

            # Stop if we hit an oversized sublist
            if current.category == "oversized":
                break

            # Check if current sublist fits completely on current sheet
            available_space = self.labels_per_sheet - len(current_sheet_data)

            # Need separator space if sheet already has content
            separator_space = 0
            if current_sheet_data:
                separator_space = self.cols
                # Extra padding for very small previous sublists
                if sheets or any(
                    len(d.get("name", "")) > 0 for d in current_sheet_data[-3:]
                ):
                    # Check if last few items were from a small sublist
                    non_empty_recent = [
                        d for d in current_sheet_data[-6:] if d.get("name")
                    ]
                    if len(non_empty_recent) <= 2 and non_empty_recent:
                        separator_space += self.cols

            space_needed = current.size + separator_space

            if space_needed <= available_space:
                # Fits completely - add with separator
                if current_sheet_data and separator_space > 0:
                    for _ in range(separator_space):
                        current_sheet_data.append({})

                current_sheet_data.extend(current.data)
                i += 1
            else:
                # Doesn't fit completely - check if we should overflow
                if current.size > self.labels_per_sheet:
                    # Large sublist that will definitely span sheets - start overflow
                    sheets_for_sublist, next_i = self._handle_overflow_sublist(
                        current, current_sheet_data, available_space - separator_space
                    )
                    sheets.extend(sheets_for_sublist)
                    current_sheet_data = []
                    i = next_i
                else:
                    # Medium sublist - finish current sheet and start new one
                    if current_sheet_data:
                        # Fill current sheet and save it
                        while len(current_sheet_data) < self.labels_per_sheet:
                            current_sheet_data.append({})

                        sheets.append(
                            {
                                "data": current_sheet_data,
                                "format": "row",
                                "sublists_info": [],  # Will be calculated separately
                                "efficiency": sum(1 for d in current_sheet_data if d)
                                / self.labels_per_sheet,
                            }
                        )
                        current_sheet_data = []

                    # Start new sheet with this sublist
                    current_sheet_data.extend(current.data)
                    i += 1

        # Handle remaining sheet data
        if current_sheet_data:
            while len(current_sheet_data) < self.labels_per_sheet:
                current_sheet_data.append({})

            sheets.append(
                {
                    "data": current_sheet_data,
                    "format": "row",
                    "sublists_info": [],
                    "efficiency": sum(1 for d in current_sheet_data if d)
                    / self.labels_per_sheet,
                }
            )

        # If no sheets created, create at least one with first sublist
        if not sheets and start_idx < len(processed_sublists):
            current = processed_sublists[start_idx]
            sheet_data = list(current.data)
            while len(sheet_data) < self.labels_per_sheet:
                sheet_data.append({})

            sheets.append(
                {
                    "data": sheet_data,
                    "format": "row",
                    "sublists_info": [(current.original_index, current.size)],
                    "efficiency": current.size / self.labels_per_sheet,
                }
            )
            i = start_idx + 1

        return sheets, i

    def _handle_overflow_sublist(
        self,
        sublist: ProcessedSublist,
        current_sheet_data: List[Dict],
        available_space: int,
    ) -> Tuple[List[Dict], int]:
        """
        Handle a large sublist that spans multiple sheets, using available space efficiently.
        """
        sheets = []
        remaining_data = list(sublist.data)

        # First, use available space on current sheet
        if available_space > 0 and current_sheet_data:
            # Add separator padding (5 labels as mentioned in requirements)
            separator_padding = min(5, available_space)
            for _ in range(separator_padding):
                current_sheet_data.append({})
            available_space -= separator_padding

            # Fill remaining space with sublist data
            if available_space > 0:
                items_for_current_sheet = min(available_space, len(remaining_data))
                current_sheet_data.extend(remaining_data[:items_for_current_sheet])
                remaining_data = remaining_data[items_for_current_sheet:]

            # Complete current sheet
            while len(current_sheet_data) < self.labels_per_sheet:
                current_sheet_data.append({})

            sheets.append(
                {
                    "data": current_sheet_data,
                    "format": "row",
                    "sublists_info": [
                        (sublist.original_index, items_for_current_sheet)
                    ],
                    "efficiency": sum(1 for d in current_sheet_data if d)
                    / self.labels_per_sheet,
                    "overflow_start": True,
                }
            )

        # Continue with remaining data on new sheets
        while remaining_data:
            sheet_data = []
            items_to_take = min(len(remaining_data), self.labels_per_sheet)
            sheet_data.extend(remaining_data[:items_to_take])
            remaining_data = remaining_data[items_to_take:]

            # Fill remaining positions
            while len(sheet_data) < self.labels_per_sheet:
                sheet_data.append({})

            is_continuation = len(sheets) > 0 or current_sheet_data
            sheets.append(
                {
                    "data": sheet_data,
                    "format": "row",
                    "sublists_info": [(sublist.original_index, items_to_take)],
                    "efficiency": items_to_take / self.labels_per_sheet,
                    "overflow_continuation": is_continuation,
                }
            )

        return sheets, 1  # Processed one sublist

    def _handle_oversized_sublist(
        self, processed_sublists: List[ProcessedSublist], start_idx: int
    ) -> Tuple[List[Dict], int]:
        """
        Handle sublists that are larger than one sheet (>30 labels).
        """
        oversized = processed_sublists[start_idx]
        sheets = []
        remaining_data = list(oversized.data)

        while remaining_data:
            sheet_data = []

            # Take up to labels_per_sheet items
            items_to_take = min(len(remaining_data), self.labels_per_sheet)
            sheet_data.extend(remaining_data[:items_to_take])
            remaining_data = remaining_data[items_to_take:]

            # Fill remaining positions
            while len(sheet_data) < self.labels_per_sheet:
                sheet_data.append({})

            sheets.append(
                {
                    "data": sheet_data,
                    "format": "row",
                    "sublists_info": [(oversized.original_index, items_to_take)],
                    "efficiency": items_to_take / self.labels_per_sheet,
                }
            )

        return sheets, start_idx + 1

    def _convert_sheets_to_row_order(self, sheets: List[Dict]) -> List[Dict]:
        """
        Convert all sheets to final row order.
        """
        result = []

        for sheet in sheets:
            if sheet["format"] == "row":
                result.extend(sheet["data"])
            else:
                # Convert from column order to row order
                converted = self._convert_column_to_row_order(sheet["data"])
                result.extend(converted)

        return result

    def _convert_column_to_row_order(self, sheet_data: List[Dict]) -> List[Dict]:
        """
        Convert a single sheet from column order to row order.
        """
        result = []

        for row in range(self.rows):
            for col in range(self.cols):
                pos = col * self.rows + row
                if pos < len(sheet_data):
                    result.append(sheet_data[pos])
                else:
                    result.append({})

        return result

    def print_optimization_summary(self, sublists: List[List[Dict]]):
        """
        Print detailed summary of the optimization strategy.
        """
        processed_sublists = self._categorize_and_sort_sublists(sublists)

        print("=== LABEL ORGANIZATION SUMMARY ===")
        print(f"Total sublists: {len([s for s in sublists if s])}")
        print(f"Total labels: {sum(len(s) for s in sublists)}")
        print()

        # Show categorization
        categories = {"small": [], "medium": [], "large": [], "oversized": []}
        for ps in processed_sublists:
            categories[ps.category].append(ps.size)

        for category, sizes in categories.items():
            if sizes:
                print(
                    f"{category.upper()} sublists (<10, 10-20, 21-30, >30): {len(sizes)} sublists"
                )
                print(f"  Sizes: {sizes}")
                print(f"  Total labels: {sum(sizes)}")
                print()

        # Show packing simulation
        sheets = self._pack_with_small_first_strategy(processed_sublists)

        print("=== SHEET LAYOUT ===")
        total_efficiency = 0

        for i, sheet in enumerate(sheets, 1):
            efficiency = sheet["efficiency"]
            total_efficiency += efficiency

            print(f"Sheet {i}: {sheet['format'].upper()} packing")
            print(f"  Sublists: {len(sheet['sublists_info'])} sublists")
            print(f"  Sizes: {[size for _, size in sheet['sublists_info']]}")

            if sheet["format"] == "column":
                columns_used = sheet.get("columns_used", len(sheet["sublists_info"]))
                print(f"  Columns used: {columns_used}/{self.cols}")
                print(f"  Each sublist fills complete column with padding")
            else:
                if sheet.get("overflow_start"):
                    print(f"  Overflow: Large sublist started with 5-label separator")
                elif sheet.get("overflow_continuation"):
                    print(f"  Overflow: Continuation of large sublist")
                elif sheet.get("has_clean_separators"):
                    print(f"  Extra padding added for clean cutting lines")

            print(
                f"  Efficiency: {efficiency:.1%} ({int(efficiency * self.labels_per_sheet)}/{self.labels_per_sheet} labels)"
            )
            print()

        if sheets:
            avg_efficiency = total_efficiency / len(sheets)
            print(f"Overall efficiency: {avg_efficiency:.1%}")
            print(f"Total sheets needed: {len(sheets)}")


# Test with the real data
if __name__ == "__main__":
    optimizer = SmallFirstLabelOrganizer()

    # Real data case with the problematic small sublists
    sublist_lengths = [34, 6, 10, 2, 72, 66, 58, 34, 2]

    # Create test sublists with actual label data
    test_sublists = []
    for i, length in enumerate(sublist_lengths):
        sublist = [
            {"name": f"Group{i}_Item{j}", "id": f"{i}_{j}"} for j in range(length)
        ]
        test_sublists.append(sublist)

    print(f"Original sublist order: {sublist_lengths}")
    print(f"Total labels: {sum(sublist_lengths)}")
    print()

    optimizer.print_optimization_summary(test_sublists)

    # Show the actual optimization
    print("\n=== ACTUAL ORGANIZATION ===")
    organized_labels = optimizer.organize_labels(test_sublists)

    # Count non-empty labels per sheet
    labels_per_sheet = optimizer.labels_per_sheet
    for sheet_num in range(len(organized_labels) // labels_per_sheet):
        start_idx = sheet_num * labels_per_sheet
        end_idx = start_idx + labels_per_sheet
        sheet_labels = organized_labels[start_idx:end_idx]

        non_empty = sum(1 for label in sheet_labels if label)
        print(
            f"Sheet {sheet_num + 1}: {non_empty}/{labels_per_sheet} labels used ({non_empty/labels_per_sheet:.1%})"
        )
