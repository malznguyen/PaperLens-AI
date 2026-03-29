import { PlaceholderPage } from "@/components/placeholder-page";

export default function WorkspacePage() {
  return (
    <PlaceholderPage
      title="Paper Workspace"
      description="This workspace is reserved for paper queues, PDF cache states, parsing progress, and future chunk inspection."
      endpoint="POST /api/ingest"
      highlights={[
        "Track selected papers and ingestion readiness",
        "Display local caching and parse status by paper",
        "Expose later evidence previews and metadata integrity checks",
      ]}
    />
  );
}
