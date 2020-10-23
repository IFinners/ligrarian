#!/usr/bin/env python3

"""Tests for the openpyxl, spreadsheet related functions of ligrarian.py."""

import unittest.mock as mock

import ligrarian


class FakeCell:
    """A fake version of openpyxl's workbook.sheet.cell."""

    def __init__(self, row, column):
        self.row = row
        self.column = column
        self.value = "not blank"
        self.set_value()

    def set_value(self):
        """Set self.value to None for cell(3, 1) to simulate blank row."""
        if self.row == 3 and self.column == 1:
            self.value = None


def test_first_blank_row():
    """Return row where cell.value is an empty string."""
    mock_sheet = mock.MagicMock()
    mock_sheet.cell.side_effect = [
            FakeCell(1, 1), FakeCell(2, 1), FakeCell(3, 1)
    ]
    assert ligrarian.first_blank_row(mock_sheet) == 3


@mock.patch('ligrarian.openpyxl')
class TestCheckYearSheetExists:
    """create_sheet only if no year_sheet in workbook, return workbook."""

    @mock.patch('ligrarian.create_sheet')
    def test_year_sheet_exists_no_create_call(self, mock_create, mock_pyxl):
        """No call to create_sheet."""
        mock_pyxl.load_workbook.return_value.sheetnames = ['2019', '2020']
        ligrarian.check_year_sheet_exists('', '2020')

        mock_create.assert_not_called()

    @mock.patch('ligrarian.create_sheet')
    def test_year_sheet_not_exist_create_call(self, mock_create, mock_pyxl):
        """One call to create_sheet."""
        mock_pyxl.load_workbook.return_value.sheetnames = ['2018', '2019']
        ligrarian.check_year_sheet_exists('', '2020')

        mock_create.assert_called_once()

    def test_workbook_returned(self, mock_pyxl):
        """Mocked workbook (load_workbook()) returned."""
        mock_workbook = mock_pyxl.load_workbook()
        mock_pyxl.load_workbook.return_value.sheetnames = ['2020']
        returned_workbook = ligrarian.check_year_sheet_exists('', '2020')

        assert returned_workbook == mock_workbook


@mock.patch('ligrarian.openpyxl')
@mock.patch('ligrarian.first_blank_row', return_value=2)
class TestCreateSheet:
    """Copies then renames sheet, blanks all but first, sets date function."""

    def test_copies_sheet(self, mock_first, mock_pyxl):
        """Should call copy_worksheet on workbook object."""
        ligrarian.create_sheet(ligrarian.openpyxl, 'copy', 'new')

        ligrarian.openpyxl.copy_worksheet.assert_called_once()

    def test_names_sheet(self, mock_first, mock_pyxl):
        """Should name sheet to new_sheet_name argument."""
        ligrarian.create_sheet(ligrarian.openpyxl, 'copy', 'new')

        assert ligrarian.openpyxl.copy_worksheet.return_value.title == 'new'

    def test_first_row_cells_not_modified(self, mock_first, mock_pyxl):
        """First row not accessed by cell call for .value modification.

        Cells are blanked by setting their .value attributes to None. This
        requires the cell to be accessed via a call with row and column args;
        so no call to row 1 column 2 indicates that the first row hasn't been
        set to None.

        """
        mock_sheet = ligrarian.openpyxl.copy_worksheet
        ligrarian.create_sheet(ligrarian.openpyxl, 'copy', 'new')
        cell_calls = mock_sheet.return_value.cell.call_args_list

        assert mock.call(row=1, column=2) not in cell_calls

    def test_other_row_cells_modified(self, mock_first, mock_pyxl):
        """Other rows cell's value attributes changed to None."""
        fake_two_one = FakeCell(2, 1)
        ligrarian.openpyxl.copy_worksheet.return_value.cell.side_effect = [
                fake_two_one,
                FakeCell(2, 2),
                FakeCell(2, 3),
                FakeCell(2, 4),
                FakeCell(2, 5),
                FakeCell(2, 6),
                FakeCell(5, 8),
        ]
        ligrarian.create_sheet(ligrarian.openpyxl, 'copy', 'new')
        assert fake_two_one.value is None

    def test_date_formula_written_to_last_cell(self, mock_first, mock_pyxl):
        """Cell 5, 8 equal to date formula."""
        fake_last_call = FakeCell(5, 8)
        ligrarian.openpyxl.copy_worksheet.return_value.cell.side_effect = [
                FakeCell(2, 1),
                FakeCell(2, 2),
                FakeCell(2, 3),
                FakeCell(2, 4),
                FakeCell(2, 5),
                FakeCell(2, 6),
                fake_last_call,
        ]
        ligrarian.create_sheet(ligrarian.openpyxl, 'copy', 'new')
        assert fake_last_call.value == "=(TODAY()-DATE(new,1,1))/7"


@mock.patch('ligrarian.openpyxl')
@mock.patch('ligrarian.first_blank_row', return_value=1)
class TestInputInfo:
    """Data written to 'year' and 'Overall' sheet and then workbook saved."""

    mock_info = {
            'title': "mock title",
            'author': "mock author",
            'pages': "mock pages",
            'category': "mock category",
            'genre': "mock genre"
    }

    def mock_cell_access(self, sheet_name, test_value, test_index):
        """Create FakeCell side_effect with one assigned."""
        test_value = FakeCell(9, 9)
        mock_cell = ligrarian.openpyxl[sheet_name].cell
        mock_side_effects = [FakeCell(1, 1)] * 12
        mock_side_effects[test_index] = test_value
        mock_cell.side_effect = mock_side_effects

        return (test_value, mock_cell.side_effect)

    def test_year_sheet_accessed(self, mock_first, mock_pyxl):
        """2020 called on mock_pyxl.__getitem__."""
        ligrarian.input_info(mock_pyxl, mock.MagicMock(),
                             '2020', 'path')
        assert (
            mock.call('2020') in mock_pyxl.__getitem__.call_args_list
        )

    def test_overall_sheet_accessed(self, mock_first, mock_pyxl):
        """Overall called on mock_pyxl.__getitem__."""
        ligrarian.input_info(
                mock_pyxl, mock.MagicMock(),
                '2020', 'path'
        )
        assert (
            mock.call('Overall') in
            mock_pyxl.__getitem__.call_args_list
        )

    def test_accessed_year_sheet_title_set(self, mock_first, mock_pyxl):
        """Given title written to year sheet on index call."""
        fake_title, mock_sides = self.mock_cell_access('2020',
                                                        "mock title", 0)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_title.value == "mock title"

    def test_accessed_year_sheet_author_set(self, mock_first, mock_pyxl):
        """Given author written to year sheet on index call."""
        fake_author, mock_sides = self.mock_cell_access('2020',
                                                        "mock author", 1)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_author.value == "mock author"

    def test_accessed_year_sheet_pages_set(self, mock_first, mock_pyxl):
        """Given pages written to year sheet on index call."""
        fake_pages, mock_sides = self.mock_cell_access('2020',
                                                       "mock pages", 2)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_pages.value == "mock pages"

    def test_accessed_year_sheet_category_set(self, mock_first, mock_pyxl):
        """Given category written to year sheet on index call."""
        fake_category, mock_sides = self.mock_cell_access('2020',
                                                          "mock category", 3)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_category.value == "mock category"

    def test_accessed_year_sheet_genre_set(self, mock_first, mock_pyxl):
        """Given genre written to year sheet on index call."""
        fake_genre, mock_sides = self.mock_cell_access('2020',
                                                       "mock genre", 4)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_genre.value == "mock genre"

    def test_accessed_year_sheet_date_set(self, mock_first, mock_pyxl):
        """Given date written to year sheet on index call."""
        fake_date, mock_sides = self.mock_cell_access('2020',
                                                      "mock date", 5)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_date.value == "2020"

    def test_accessed_overall_sheet_title_set(self, mock_first, mock_pyxl):
        """Given title written to Overall sheet on index call."""
        fake_title, mock_sides = self.mock_cell_access('2020',
                                                       "mock title", 6)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_title.value == "mock title"

    def test_accessed_overall_sheet_author_set(self, mock_first, mock_pyxl):
        """Given author written to Overall sheet on index call."""
        fake_author, mock_sides = self.mock_cell_access('2020',
                                                        "mock author", 7)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_author.value == "mock author"

    def test_accessed_overall_sheet_pages_set(self, mock_first, mock_pyxl):
        """Given pages written to Overall sheet on index call."""
        fake_pages, mock_sides = self.mock_cell_access('2020',
                                                       "mock pages", 8)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_pages.value == "mock pages"

    def test_accessed_overall_sheet_category_set(self, mock_first, mock_pyxl):
        """Given category written to Overall sheet on index call."""
        fake_category, mock_sides = self.mock_cell_access('2020',
                                                          "mock category", 9)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_category.value == "mock category"

    def test_accessed_overall_sheet_genre_set(self, mock_first, mock_pyxl):
        """Given genre written to Overall sheet on index call."""
        fake_genre, mock_sides = self.mock_cell_access('2020',
                                                       "mock genre", 10)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_genre.value == "mock genre"

    def test_accessed_overall_sheet_date_set(self, mock_first, mock_pyxl):
        """Given date written to Overall sheet on index call."""
        fake_date, mock_sides = self.mock_cell_access('2020', "mock date", 11)
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        assert fake_date.value == "2020"

    def test_workbook_saved(self, mock_first, mock_pyxl):
        """Save called on workbook (mock_pyxl)."""
        ligrarian.input_info(
                mock_pyxl, self.mock_info, '2020', 'path')

        mock_pyxl.save.assert_called_once()
