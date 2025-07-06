import React, { useRef, useEffect } from 'react';

interface VideoStreamModalProps {
  open: boolean;
  onClose: () => void;
  streamUrl: string;
  streamName: string;
}

function isMJPEG(url: string) {
  // crude check: if it's http and not .m3u8 or .mp4, treat as MJPEG
  return url.startsWith('http') && !url.endsWith('.m3u8') && !url.endsWith('.mp4');
}

const VideoStreamModal: React.FC<VideoStreamModalProps> = ({ open, onClose, streamUrl, streamName }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  // Stop the stream when modal closes
  useEffect(() => {
    if (!open && videoRef.current) {
      videoRef.current.pause();
      videoRef.current.src = '';
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80">
      <div className="relative w-full max-w-3xl mx-2 bg-simsy-card rounded-xl shadow-lg flex flex-col items-center p-4">
        <h2 className="text-2xl font-bold text-simsy-blue mb-4 w-full text-center">Live Stream: {streamName}</h2>
        <div className="w-full flex-1 flex items-center justify-center">
          {isMJPEG(streamUrl) ? (
            <img
              src={streamUrl}
              alt="Live Stream"
              className="w-full h-[40vw] max-h-[60vh] rounded-lg object-contain bg-black"
              style={{ maxWidth: '100%' }}
            />
          ) : (
            <video
              ref={videoRef}
              src={streamUrl}
              controls
              autoPlay
              className="w-full h-[40vw] max-h-[60vh] rounded-lg object-contain bg-black"
              style={{ maxWidth: '100%' }}
            />
          )}
        </div>
        <button
          onClick={onClose}
          className="mt-6 w-full bg-red-600 text-white font-bold py-2 px-4 rounded hover:bg-red-700 transition"
        >
          Stop
        </button>
      </div>
    </div>
  );
};

export default VideoStreamModal; 