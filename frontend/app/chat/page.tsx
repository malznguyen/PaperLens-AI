import { PlaceholderPage } from "@/components/placeholder-page";

export default function ChatPage() {
  return (
    <PlaceholderPage
      title="Research Chat"
      description="Future answers will be grounded in retrieved chunks only, with explicit citations and uncertainty when evidence is weak."
      endpoint="POST /api/chat"
      highlights={[
        "Accept research questions over ingested papers",
        "Render answer blocks with source traceability",
        "Keep the interaction focused on literature analysis instead of generic chat",
      ]}
    />
  );
}
