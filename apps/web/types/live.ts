export type ProductProfile = {
  product_name: string;
  brand?: string;
  price?: string;
  specification?: string;
  selling_points?: string[];
  promotions?: string[];
  compliance_notes?: string[];
  metadata?: Record<string, unknown>;
};

export type AudienceEvent = {
  event_id?: string;
  user_id?: string;
  user_name?: string;
  text: string;
  source?: string;
  created_at?: string;
};

export type LiveRoomSession = {
  session_id: string;
  status: string;
  product: ProductProfile;
  current_topic: string;
  event_count: number;
  reply_count: number;
  recent_replies: AnchorReply[];
};

export type AnchorReply = {
  reply_id: string;
  session_id: string;
  event_id: string;
  intent: string;
  text: string;
  compliance_passed: boolean;
  compliance_notes: string[];
  speech_artifact_id: string;
  speech_audio_url: string;
  created_at: string;
};

export type LiveEvent = {
  type: string;
  session_id: string;
  payload: Record<string, unknown>;
  created_at: string;
};
