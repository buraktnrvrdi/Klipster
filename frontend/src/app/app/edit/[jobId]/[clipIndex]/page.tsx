import ClipEditor from "@/components/ClipEditor";

export default async function EditClipPage({
  params,
}: {
  params: Promise<{ jobId: string; clipIndex: string }>;
}) {
  const { jobId, clipIndex } = await params;
  return <ClipEditor jobId={jobId} clipIndex={Number(clipIndex)} />;
}
