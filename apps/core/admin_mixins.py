import csv
from django.http import HttpResponse


class ExportCsvMixin:
    """Adds an 'Export selected to CSV' admin action exporting concrete model fields."""
    csv_filename = "export"

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = f'attachment; filename="{self.csv_filename}.csv"'
        writer = csv.writer(resp)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, f) for f in field_names])
        self.message_user(request, f"Exported {queryset.count()} row(s) to CSV.")
        return resp
    export_as_csv.short_description = "Export selected to CSV"
