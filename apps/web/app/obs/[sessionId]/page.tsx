import ObsPlayer from '@/components/obs/ObsPlayer';

export default function ObsPage({ params, searchParams }: { params: { sessionId: string }; searchParams: { autoplay?: string } }) {
  return <ObsPlayer sessionId={params.sessionId} autoplay={searchParams.autoplay !== '0'} />;
}
