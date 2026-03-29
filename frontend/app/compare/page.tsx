import { PlaceholderPage } from "@/components/placeholder-page";

export default function ComparePage() {
  return (
    <PlaceholderPage
      title="Compare Papers"
      description="Comparison mode will align multiple papers across objective, methodology, datasets, strengths, and limitations."
      endpoint="POST /api/compare"
      highlights={[
        "Select 2 to 5 ingested papers",
        "Render structured compare matrices with cited evidence",
        "Summarize overlap, disagreement, and research gaps",
      ]}
    />
  );
}
