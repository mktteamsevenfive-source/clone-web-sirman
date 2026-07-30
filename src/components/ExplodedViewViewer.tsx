'use client';

import React, { useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Maximize2, ImageOff, Loader2 } from 'lucide-react';
import { Product } from '@/lib/types';

interface ExplodedViewViewerProps {
    product: Product;
}

export const ExplodedViewViewer: React.FC<ExplodedViewViewerProps> = ({ product }) => {
    const [zoom, setZoom] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const supabaseProjectUrl = "https://ofrerwyoasklgsejlbzr.supabase.co";
    const cdnUrl = `${supabaseProjectUrl}/storage/v1/object/public/diagram_images/${product.pdf_name || product.pdfName}.png`;

    const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
    const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
    const handleReset = () => setZoom(1);

    return (
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 flex flex-col items-center justify-center relative min-h-[540px] overflow-hidden shadow-inner">
            {/* Toolbar controls */}
            <div className="absolute top-4 left-4 z-10 flex items-center gap-1 bg-white/90 backdrop-blur-md px-2 py-1.5 rounded-xl shadow-md border border-slate-200">
                <button
                    onClick={handleZoomIn}
                    className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Zoom In"
                >
                    <ZoomIn className="w-4 h-4" />
                </button>
                <button
                    onClick={handleZoomOut}
                    className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors"
                    title="Zoom Out"
                >
                    <ZoomOut className="w-4 h-4" />
                </button>
                <button
                    onClick={handleReset}
                    className="p-1.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors text-xs font-semibold px-2"
                >
                    RESET
                </button>
                <div className="w-px h-4 bg-slate-200 mx-1" />
                <span className="text-xs font-mono font-medium text-slate-500 px-1">
                    {Math.round(zoom * 100)}%
                </span>
            </div>

            {/* Loading Indicator */}
            {loading && !error && (
                <div className="flex flex-col items-center justify-center space-y-3 py-20 text-slate-500">
                    <Loader2 className="w-10 h-10 text-[#0284C7] animate-spin" />
                    <p className="text-sm font-medium">Loading high-resolution diagram from Supabase CDN...</p>
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="flex flex-col items-center justify-center py-20 text-center max-w-sm">
                    <ImageOff className="w-12 h-12 text-slate-400 mb-3" />
                    <h4 className="text-base font-semibold text-slate-800 mb-1">Diagram Image Unavailable</h4>
                    <p className="text-xs text-slate-500">
                        File: <code className="bg-slate-200 text-slate-800 px-1.5 py-0.5 rounded font-mono">{product.pdf_name || product.pdfName}.png</code>
                    </p>
                </div>
            )}

            {/* Image Canvas Viewport */}
            <div className="w-full flex items-center justify-center overflow-auto max-h-[600px] p-4">
                {/* Image */}
                <img
                    src={cdnUrl}
                    alt={`${product.model} Exploded View Technical Diagram`}
                    onLoad={() => setLoading(false)}
                    onError={() => {
                        setLoading(false);
                        setError(true);
                    }}
                    style={{ transform: `scale(${zoom})`, transition: 'transform 0.2s ease-out' }}
                    className={`max-w-full h-auto rounded-xl shadow-lg bg-white ${loading || error ? 'hidden' : 'block'}`}
                />
            </div>
        </div>
    );
};
