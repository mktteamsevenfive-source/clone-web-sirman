'use client';

import React, { useState, useEffect } from 'react';
import { ProductData } from '@/lib/data';
import { SUPABASE_CDN_BASE } from '@/lib/supabase';
import { ZoomIn, ZoomOut, FileText, Target } from 'lucide-react';

interface ClickableElement {
    itemId: string;
    matchedItemId?: number;
    transform?: string;
    x?: string;
    y?: string;
    content?: string;
}

interface HotspotData {
    width: number;
    height: number;
    transform?: string;
    clickableElements: ClickableElement[];
}

interface ExplodedViewViewerProps {
    product: ProductData;
    selectedRef?: string | null;
    onSelectPartRef?: (ref: string) => void;
}

export const ExplodedViewViewer: React.FC<ExplodedViewViewerProps> = ({
    product,
    selectedRef,
    onSelectPartRef,
}) => {
    const [zoom, setZoom] = useState(1.0);
    const [imgError, setImgError] = useState(false);
    const [hotspotData, setHotspotData] = useState<HotspotData | null>(null);
    const [hoveredRef, setHoveredRef] = useState<string | null>(null);

    const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 3.0));
    const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.25));
    const handleZoomReset = () => setZoom(1.0);

    const pdfFilename = product.pdf_name || (product as any).pdfName;
    const cleanPdfName = pdfFilename ? pdfFilename.replace('.pdf', '').replace('.png', '') : '';
    
    const realDiagramImageUrl = pdfFilename
        ? `${SUPABASE_CDN_BASE}/${pdfFilename}.png`
        : null;

    // Load Hotspot JSON
    useEffect(() => {
        if (!cleanPdfName) {
            setHotspotData(null);
            return;
        }

        let isMounted = true;
        fetch(`/hotspots/${cleanPdfName}.json`)
            .then((res) => {
                if (res.ok) return res.json();
                throw new Error('Hotspot not found');
            })
            .then((data) => {
                if (isMounted) {
                    const parsed = typeof data === 'string' ? JSON.parse(data) : data;
                    setHotspotData(parsed);
                }
            })
            .catch(() => {
                if (isMounted) setHotspotData(null);
            });

        return () => {
            isMounted = false;
        };
    }, [cleanPdfName]);

    const VIEWPORT_HEIGHT = 520;

    // Helper to extract ref number from element
    const getRefFromElement = (elem: ClickableElement): string => {
        if (elem.matchedItemId !== undefined) return String(elem.matchedItemId);
        if (elem.itemId) return String(elem.itemId);
        return '';
    };

    // Helper to check if ref matches selected or hovered ref
    const isRefMatched = (elemRef: string, targetRef: string | null | undefined): boolean => {
        if (!targetRef || !elemRef) return false;
        const normElem = elemRef.replace(/^0+/, '');
        const normTarget = targetRef.replace(/^0+/, '');
        return normElem === normTarget;
    };

    // Helper to parse transform matrix coordinates (x, y)
    const parseTransformMatrix = (matrixStr?: string) => {
        if (!matrixStr) return { x: 0, y: 0 };
        const match = matrixStr.match(/matrix\(([^)]+)\)/);
        if (match) {
            const parts = match[1].split(',').map((v) => floatVal(v.trim()));
            if (parts.length >= 6) {
                return { x: parts[4], y: parts[5] };
            }
        }
        return { x: 0, y: 0 };
    };

    const floatVal = (val: string) => {
        const parsed = parseFloat(val);
        return isNaN(parsed) ? 0 : parsed;
    };

    // Find matching part name for tooltip
    const getPartNameForRef = (ref: string) => {
        if (!product.parts) return '';
        const found = product.parts.find((p) => isRefMatched(p.ref || '', ref));
        return found ? found.name : '';
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            background: '#fff',
            border: '1px solid #e2e8f0',
            borderRadius: '1rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            height: '100%',
        }}>
            {/* Toolbar */}
            <div style={{
                flexShrink: 0,
                padding: '0.75rem',
                background: '#f8fafc',
                borderBottom: '1px solid #e2e8f0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '0.5rem',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {pdfFilename && (
                        <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.375rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: '#1d4ed8',
                            background: '#eff6ff',
                            border: '1px solid #bfdbfe',
                            padding: '0.25rem 0.625rem',
                            borderRadius: '0.5rem',
                        }}>
                            <FileText style={{ width: '0.875rem', height: '0.875rem' }} />
                            {pdfFilename}
                        </span>
                    )}

                    {hotspotData && (
                        <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            color: '#059669',
                            background: '#ecfdf5',
                            border: '1px solid #a7f3d0',
                            padding: '0.25rem 0.625rem',
                            borderRadius: '0.5rem',
                        }}>
                            <Target style={{ width: '0.875rem', height: '0.875rem' }} />
                            {hotspotData.clickableElements.length} Interactive Hotspots
                        </span>
                    )}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <button onClick={handleZoomIn} title="Zoom In" style={{ padding: '0.375rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer', display: 'flex' }}>
                        <ZoomIn style={{ width: '1rem', height: '1rem' }} />
                    </button>
                    <button onClick={handleZoomOut} title="Zoom Out" style={{ padding: '0.375rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer', display: 'flex' }}>
                        <ZoomOut style={{ width: '1rem', height: '1rem' }} />
                    </button>
                    <button onClick={handleZoomReset} title="Reset" style={{ padding: '0.25rem 0.625rem', fontSize: '0.75rem', fontWeight: 700, background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer' }}>
                        RESET
                    </button>
                </div>
            </div>

            {/* Diagram Viewport */}
            <div style={{
                position: 'relative',
                width: '100%',
                height: `${VIEWPORT_HEIGHT}px`,
                overflow: 'hidden',
                background: '#f8fafc',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
            }}>
                {/* Scale wrapper */}
                <div style={{
                    transform: `scale(${zoom})`,
                    transformOrigin: 'center center',
                    transition: 'transform 0.18s ease-out',
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                    overflow: 'hidden',
                }}>
                    {realDiagramImageUrl && !imgError ? (
                        <div style={{
                            position: 'relative',
                            display: 'inline-block',
                            maxHeight: `${VIEWPORT_HEIGHT - 24}px`,
                            maxWidth: '100%',
                        }}>
                            <img
                                src={realDiagramImageUrl}
                                alt={`Exploded Diagram - ${product.model}`}
                                onError={() => setImgError(true)}
                                style={{
                                    display: 'block',
                                    maxHeight: `${VIEWPORT_HEIGHT - 24}px`,
                                    maxWidth: '100%',
                                    width: 'auto',
                                    height: 'auto',
                                    objectFit: 'contain',
                                    userSelect: 'none',
                                }}
                            />

                            {/* Hotspot Overlay SVG */}
                            {hotspotData && (
                                <svg
                                    viewBox={`0 0 ${hotspotData.width} ${hotspotData.height}`}
                                    style={{
                                        position: 'absolute',
                                        top: 0,
                                        left: 0,
                                        width: '100%',
                                        height: '100%',
                                        pointerEvents: 'auto',
                                    }}
                                >
                                    <g transform={hotspotData.transform || undefined}>
                                        {hotspotData.clickableElements.map((elem, idx) => {
                                            const elemRef = getRefFromElement(elem);
                                            const isSelected = isRefMatched(elemRef, selectedRef);
                                            const isHovered = isRefMatched(elemRef, hoveredRef);
                                            const isActive = isSelected || isHovered;
                                            const coords = parseTransformMatrix(elem.transform);

                                            return (
                                                <g
                                                    key={idx}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (elemRef && onSelectPartRef) {
                                                            onSelectPartRef(elemRef);
                                                        }
                                                    }}
                                                    onMouseEnter={() => setHoveredRef(elemRef)}
                                                    onMouseLeave={() => setHoveredRef(null)}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    {/* Custom rendered interactive hotspot circle */}
                                                    <circle
                                                        cx={coords.x}
                                                        cy={coords.y}
                                                        r={isActive ? 16 : 11}
                                                        fill={isActive ? '#C8102E' : 'rgba(29, 78, 216, 0.18)'}
                                                        stroke={isActive ? '#ffffff' : '#1d4ed8'}
                                                        strokeWidth={isActive ? 2.5 : 1.5}
                                                        style={{
                                                            transition: 'all 0.15s ease',
                                                            filter: isActive ? 'drop-shadow(0 2px 4px rgba(200,16,46,0.5))' : 'none',
                                                        }}
                                                    />
                                                    <text
                                                        x={coords.x}
                                                        y={coords.y}
                                                        textAnchor="middle"
                                                        dominantBaseline="central"
                                                        fontSize={isActive ? 10 : 8}
                                                        fontWeight="bold"
                                                        fill={isActive ? '#ffffff' : '#1e293b'}
                                                        style={{ pointerEvents: 'none', userSelect: 'none' }}
                                                    >
                                                        {elemRef}
                                                    </text>

                                                    {/* Tooltip on hover */}
                                                    {isHovered && (
                                                        <g transform={`translate(${coords.x + 18}, ${coords.y - 12})`}>
                                                            <rect
                                                                x="0"
                                                                y="0"
                                                                width={Math.max(120, getPartNameForRef(elemRef).length * 7)}
                                                                height="24"
                                                                rx="6"
                                                                fill="#0f172a"
                                                                opacity="0.9"
                                                            />
                                                            <text
                                                                x="8"
                                                                y="15"
                                                                fontSize="9"
                                                                fontWeight="600"
                                                                fill="#ffffff"
                                                            >
                                                                Ref #{elemRef}: {getPartNameForRef(elemRef).slice(0, 20)}
                                                            </text>
                                                        </g>
                                                    )}
                                                </g>
                                            );
                                        })}
                                    </g>
                                </svg>
                            )}
                        </div>
                    ) : (
                        <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                            No diagram image available for {product.model}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
