import { PlaceholderPage } from "@/components/placeholder-page";

export default function SearchPage() {
  return (
    <PlaceholderPage
      title="Search Papers"
      description="Topic search will arrive in Phase 2 with arXiv-backed metadata results, abstracts, and selection controls."
      endpoint="POST /api/search-papers"
      highlights={[
        "Shortlist topic queries and max result counts",
        "Render normalized metadata cards with abstracts",
        "Promote selected papers into the ingestion workspace",
      ]}
    />
  );
}
