import { motion } from 'framer-motion';
import { Video } from 'lucide-react';
import { LiveVideoMonitoring } from '@/pages/Safety/LiveVideoMonitoring';

export default function VideoSurveillancePage() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
      <div className="page-header">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="badge bg-primary-500/20 text-primary-300 border border-primary-500/30">
              Computer Vision & Edge Feeds
            </span>
          </div>
          <h1 className="page-title flex items-center gap-2.5">
            <Video className="text-primary-400" size={24} />
            Video Surveillance
          </h1>
          <p className="page-subtitle">Real-time CCTV and RTSP video stream monitoring with automated zone intrusion and hazard detection</p>
        </div>
      </div>
      <LiveVideoMonitoring />
    </motion.div>
  );
}
