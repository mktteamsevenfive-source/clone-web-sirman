'use client';

import React, { useState, useEffect, useRef } from 'react';
import { ProductData } from '@/lib/data';
import { SUPABASE_CDN_BASE } from '@/lib/supabase';
import { ZoomIn, ZoomOut, FileText, Target, Hand, RotateCcw } from 'lucide-react';

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
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [isDragging, setIsDragging] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [panStart, setPanStart] = useState({ x: 0, y: 0 });

    const [isSpacePressed, setIsSpacePressed] = useState(false);
    const [isHandMode, setIsHandMode] = useState(false);

    const [imgError, setImgError] = useState(false);
    const [hotspotData, setHotspotData] = useState<HotspotData | null>(null);
    const [hoveredRef, setHoveredRef] = useState<string | null>(null);

    const viewportRef = useRef<HTMLDivElement>(null);

    // Zoom handlers
    const handleZoomIn = () => setZoom((prev) => Math.min(prev + 0.25, 4.0));
    const handleZoomOut = () => setZoom((prev) => Math.max(prev - 0.25, 0.25));
    const handleReset = () => {
        setZoom(1.0);
        setPan({ x: 0, y: 0 });
    };

    // Spacebar listener for Photoshop-style pan mode
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
                e.preventDefault();
                setIsSpacePressed(true);
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            if (e.code === 'Space') {
                setIsSpacePressed(false);
                setIsDragging(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, []);

    // Multi-Diagram Views state (Table 1, Table 2, Table 3...)
    interface DiagramTable {
        id: number;
        order?: number;
        name?: string;
        pdfName?: string;
        type?: string;
    }
    const [diagramViews, setDiagramViews] = useState<DiagramTable[]>([]);
    const [activeViewIndex, setActiveViewIndex] = useState(0);

    // Fetch product_views.json for multi-diagram tables
    useEffect(() => {
        let isMounted = true;
        const loadProductViews = async () => {
            try {
                let viewsMap: Record<string, DiagramTable[]> = {};
                let res = await fetch('/product_views.json').catch(() => null);
                if (!res || !res.ok) {
                    res = await fetch('https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/product_views.json').catch(() => null);
                }
                if (res && res.ok) {
                    viewsMap = await res.json();
                }
                const prodViews = viewsMap[String(product.id)] || viewsMap[String(product.code)] || [];
                if (isMounted) {
                    setDiagramViews(prodViews);
                    setActiveViewIndex(0);
                }
            } catch {
                if (isMounted) setDiagramViews([]);
            }
        };
        loadProductViews();
        return () => {
            isMounted = false;
        };
    }, [product.id, product.code]);

    // Active Table & PDF Name resolution
    const activeTable = diagramViews[activeViewIndex] || null;
    const pdfFilename = activeTable?.pdfName || product.pdf_name || (product as any).pdfName;
    const cleanPdfName = pdfFilename ? pdfFilename.replace(/\.pdf$/i, '').replace(/\.png$/i, '') : '';
    const viewId = activeTable?.id || product.exploded_view_id || (product as any).explodedViewId || product.id;

    // Image fallback sequence
    const [imgSourceIndex, setImgSourceIndex] = useState(0);

    const possibleImageUrls = React.useMemo(() => {
        const urls: string[] = [];
        const tableName = activeTable?.name || '';
        const cleanTableName = tableName ? tableName.replace(/ /g, '_').toLowerCase() : '';

        if (pdfFilename) {
            urls.push(`${SUPABASE_CDN_BASE}/${pdfFilename}.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${pdfFilename}`);
            urls.push(`${SUPABASE_CDN_BASE}/${pdfFilename.toLowerCase()}.png`);
        }
        if (cleanPdfName) {
            urls.push(`${SUPABASE_CDN_BASE}/${cleanPdfName}.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${cleanPdfName.toLowerCase()}.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${cleanPdfName}.pdf.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${cleanPdfName.toLowerCase()}.pdf.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${cleanPdfName.replace(/ /g, '_')}.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${cleanPdfName.replace(/ /g, '_').toLowerCase()}.png`);
            urls.push(`/diagram_images/${cleanPdfName}.png`);
            urls.push(`/diagram_images/${cleanPdfName.toLowerCase()}.png`);
            urls.push(`/diagram_images/${cleanPdfName}.pdf.png`);
        }
        if (cleanTableName) {
            urls.push(`${SUPABASE_CDN_BASE}/${cleanTableName}.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${cleanTableName}.pdf.png`);
        }
        if (viewId) {
            urls.push(`${SUPABASE_CDN_BASE}/${viewId}.png`);
            urls.push(`${SUPABASE_CDN_BASE}/${viewId}.jpg`);
            urls.push(`/diagram_images/${viewId}.png`);
        }
        if (product.id) {
            urls.push(`${SUPABASE_CDN_BASE}/${product.id}.png`);
        }
        return Array.from(new Set(urls.filter(Boolean)));
    }, [pdfFilename, cleanPdfName, viewId, product.id, activeTable?.name]);

    const currentDiagramUrl = possibleImageUrls[imgSourceIndex] || null;

    useEffect(() => {
        setImgSourceIndex(0);
        setImgError(false);
    }, [product.id, pdfFilename]);

    const handleImageError = () => {
        if (imgSourceIndex < possibleImageUrls.length - 1) {
            setImgSourceIndex((prev) => prev + 1);
        } else {
            setImgError(true);
        }
    };

    useEffect(() => {
        if (!cleanPdfName) {
            setHotspotData(null);
            return;
        }

        let isMounted = true;

        const loadHotspot = async () => {
            try {
                // 1. Load index mapping if available
                let resolvedName = `${cleanPdfName}.json`;
                try {
                    let idxRes = await fetch('/hotspots/index.json').catch(() => null);
                    if (!idxRes || !idxRes.ok) {
                        idxRes = await fetch('https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/index.json').catch(() => null);
                    }
                    if (idxRes && idxRes.ok) {
                        const indexMap = await idxRes.json();
                        const mapped = indexMap[cleanPdfName] || indexMap[cleanPdfName.replace(/ /g, '_')];
                        if (mapped) resolvedName = mapped;
                    }
                } catch {
                    // ignore index error, fallback to direct filename
                }

                const cleanSafe = cleanPdfName.replace(/ /g, '_');
                const urlsToTry = Array.from(new Set([
                    `/hotspots/${resolvedName}`,
                    `/hotspots/${cleanPdfName}.json`,
                    `/hotspots/${cleanSafe}.json`,
                    `https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/${resolvedName}`,
                    `https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/${cleanPdfName}.json`,
                    `https://ofrerwyoasklgsejlbzr.supabase.co/storage/v1/object/public/diagram_hotspots/${cleanSafe}.json`
                ]));

                let loadedData = null;
                for (const url of urlsToTry) {
                    try {
                        const res = await fetch(url);
                        if (res.ok) {
                            loadedData = await res.json();
                            break;
                        }
                    } catch {
                        // continue trying next URL
                    }
                }

                if (isMounted) {
                    if (loadedData) {
                        const parsed = typeof loadedData === 'string' ? JSON.parse(loadedData) : loadedData;
                        setHotspotData(parsed);
                    } else {
                        setHotspotData(null);
                    }
                }
            } catch {
                if (isMounted) setHotspotData(null);
            }
        };

        loadHotspot();

        return () => {
            isMounted = false;
        };
    }, [cleanPdfName]);

    const VIEWPORT_HEIGHT = 520;

    // Pan Drag handlers
    const canPan = isSpacePressed || isHandMode || zoom > 1.0;

    const handleMouseDown = (e: React.MouseEvent) => {
        if (canPan || e.button === 1) { // Left click in pan mode OR middle click
            e.preventDefault();
            setIsDragging(true);
            setDragStart({ x: e.clientX, y: e.clientY });
            setPanStart({ x: pan.x, y: pan.y });
        }
    };

    const handleMouseMove = (e: React.MouseEvent) => {
        if (isDragging) {
            e.preventDefault();
            const dx = e.clientX - dragStart.x;
            const dy = e.clientY - dragStart.y;
            setPan({
                x: panStart.x + dx,
                y: panStart.y + dy,
            });
        }
    };

    const handleMouseUp = () => {
        setIsDragging(false);
    };

    // Wheel zoom
    const handleWheel = (e: React.WheelEvent) => {
        if (e.ctrlKey || e.metaKey || canPan) {
            e.preventDefault();
            const delta = e.deltaY < 0 ? 0.15 : -0.15;
            setZoom((prev) => Math.min(Math.max(prev + delta, 0.25), 4.0));
        }
    };

    // Helper to extract ref number from element (prefer itemId to preserve 74A, 74B, 75A suffixes)
    const getRefFromElement = (elem: ClickableElement): string => {
        if (elem.itemId) return String(elem.itemId);
        if (elem.matchedItemId !== undefined) return String(elem.matchedItemId);
        return '';
    };

    // Helper to check if ref matches selected or hovered ref
    const isRefMatched = (elemRef: string, targetRef: string | null | undefined): boolean => {
        if (!targetRef || !elemRef) return false;
        const normElem = elemRef.trim().toUpperCase().replace(/^0+/, '');
        const normTarget = targetRef.trim().toUpperCase().replace(/^0+/, '');
        
        // 1. Exact match (74A === 74A)
        if (normElem === normTarget) return true;

        // 2. If both have letters and letters differ (e.g. 74A vs 74B), DO NOT MATCH!
        const elemHasLetter = /[A-Z]$/.test(normElem);
        const targetHasLetter = /[A-Z]$/.test(normTarget);
        if (elemHasLetter && targetHasLetter) {
            return false;
        }

        // 3. Fallback match if one is pure number (e.g. 74A vs 74)
        const baseElem = normElem.replace(/[A-Z]$/, '');
        const baseTarget = normTarget.replace(/[A-Z]$/, '');
        return baseElem === baseTarget;
    };



    // Helper to parse transform matrix coordinates (x, y)
    // Handles BOTH comma-separated: matrix(1,0,0,-1,tx,ty)  AND  space-separated: matrix(1 0 0 1 tx ty)
    const parseTransformMatrix = (matrixStr?: string) => {
        if (!matrixStr) return { x: 0, y: 0 };
        const match = matrixStr.match(/matrix\(([^)]+)\)/);
        if (match) {
            const parts = match[1].split(/[,\s]+/).map((v) => floatVal(v.trim())).filter((_, i, arr) => arr.length > 1 || i === 0);
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

    // Detect if root hotspot transform flips Y axis (negative Y scale = PDF coordinate system)
    // If flipped, text needs scale(1,-1) to read right-side-up
    const rootYScale = React.useMemo(() => {
        if (!hotspotData?.transform) return 1;
        const match = hotspotData.transform.match(/matrix\(([^)]+)\)/);
        if (match) {
            const parts = match[1].split(/[,\s]+/).map((v) => floatVal(v.trim()));
            if (parts.length >= 6) return parts[3]; // d = Y-scale in matrix(a b c d e f)
        }
        return 1;
    }, [hotspotData?.transform]);
    const isYFlipped = rootYScale < 0;

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
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
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

                    {/* Spacebar Indicator */}
                    {isSpacePressed && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-md animate-pulse">
                            <Hand className="w-3.5 h-3.5 text-amber-600" /> Spacebar Pan Mode
                        </span>
                    )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    {/* Hand Tool Toggle Button */}
                    <button
                        onClick={() => setIsHandMode(!isHandMode)}
                        title="Hand Pan Tool (Hold Spacebar)"
                        style={{
                            padding: '0.375rem 0.5rem',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            background: isHandMode || isSpacePressed ? '#fee2e2' : '#fff',
                            color: isHandMode || isSpacePressed ? '#c8102e' : '#475569',
                            border: isHandMode || isSpacePressed ? '1px solid #fca5a5' : '1px solid #e2e8f0',
                            borderRadius: '0.5rem',
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.25rem',
                            transition: 'all 0.15s ease',
                        }}
                    >
                        <Hand style={{ width: '0.875rem', height: '0.875rem' }} />
                        Hand Mode
                    </button>

                    <div className="h-4 w-px bg-slate-200 mx-0.5" />

                    <button onClick={handleZoomIn} title="Zoom In" style={{ padding: '0.375rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer', display: 'flex' }}>
                        <ZoomIn style={{ width: '1rem', height: '1rem' }} />
                    </button>
                    <button onClick={handleZoomOut} title="Zoom Out" style={{ padding: '0.375rem', background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer', display: 'flex' }}>
                        <ZoomOut style={{ width: '1rem', height: '1rem' }} />
                    </button>
                    <button onClick={handleReset} title="Reset Zoom & Pan" style={{ padding: '0.25rem 0.625rem', fontSize: '0.75rem', fontWeight: 700, background: '#fff', border: '1px solid #e2e8f0', borderRadius: '0.5rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                        <RotateCcw style={{ width: '0.75rem', height: '0.75rem' }} />
                        RESET
                    </button>
                </div>
            </div>

            {/* Multi-Diagram Table Selector Bar */}
            {diagramViews.length > 1 && (
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 0.75rem',
                    background: '#f1f5f9',
                    borderBottom: '1px solid #e2e8f0',
                    overflowX: 'auto',
                }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#475569', whiteSpace: 'nowrap' }}>
                        Diagram Tables ({diagramViews.length}):
                    </span>
                    {diagramViews.map((table, idx) => {
                        const isActive = idx === activeViewIndex;
                        return (
                            <button
                                key={table.id || idx}
                                onClick={() => {
                                    setActiveViewIndex(idx);
                                    setImgSourceIndex(0);
                                    setImgError(false);
                                }}
                                style={{
                                    padding: '0.375rem 0.75rem',
                                    fontSize: '0.75rem',
                                    fontWeight: isActive ? 800 : 600,
                                    color: isActive ? '#fff' : '#334155',
                                    background: isActive ? '#C8102E' : '#fff',
                                    border: isActive ? '1px solid #C8102E' : '1px solid #cbd5e1',
                                    borderRadius: '0.5rem',
                                    cursor: 'pointer',
                                    whiteSpace: 'nowrap',
                                    boxShadow: isActive ? '0 2px 4px rgba(200,16,46,0.3)' : 'none',
                                    transition: 'all 0.15s ease',
                                }}
                            >
                                Table {table.order || idx + 1}: {table.name || `View ${idx + 1}`}
                            </button>
                        );
                    })}
                </div>
            )}

            {/* Diagram Viewport Container */}
            <div
                ref={viewportRef}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
                onWheel={handleWheel}
                style={{
                    position: 'relative',
                    width: '100%',
                    height: `${VIEWPORT_HEIGHT}px`,
                    overflow: 'hidden',
                    background: '#f8fafc',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: isDragging ? 'grabbing' : canPan ? 'grab' : 'default',
                    userSelect: 'none',
                }}
            >
                {/* Scale and Pan Transform Wrapper */}
                <div style={{
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transformOrigin: 'center center',
                    transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                    width: '100%',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative',
                }}>
                    {currentDiagramUrl && !imgError ? (
                        <div style={{
                            position: 'relative',
                            display: 'inline-block',
                            maxHeight: `${VIEWPORT_HEIGHT - 24}px`,
                            maxWidth: '100%',
                        }}>
                            <img
                                src={currentDiagramUrl}
                                alt={`Exploded Diagram - ${product.model}`}
                                onError={handleImageError}
                                style={{
                                    display: 'block',
                                    maxHeight: `${VIEWPORT_HEIGHT - 24}px`,
                                    maxWidth: '100%',
                                    width: 'auto',
                                    height: 'auto',
                                    objectFit: 'contain',
                                    userSelect: 'none',
                                    pointerEvents: 'none',
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
                                            const isLongRef = elemRef.length > 2;
                                            const radius = isActive ? (isLongRef ? 19 : 17) : (isLongRef ? 13.5 : 11);
                                            const fontSz = isActive ? (isLongRef ? 9.5 : 11) : (isLongRef ? 7.5 : 9);
                                            const coords = parseTransformMatrix(elem.transform);


                                            return (
                                                <g
                                                    key={idx}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (elemRef && onSelectPartRef && !isDragging) {
                                                            onSelectPartRef(elemRef);
                                                        }
                                                    }}
                                                    onMouseEnter={() => setHoveredRef(elemRef)}
                                                    onMouseLeave={() => setHoveredRef(null)}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    {/* Outer Ring & Circle */}
                                                    <circle
                                                        cx={coords.x}
                                                        cy={coords.y}
                                                        r={radius}
                                                        fill={isActive ? '#C8102E' : 'rgba(37, 99, 235, 0.85)'}
                                                        stroke={isActive ? '#ffffff' : '#ffffff'}
                                                        strokeWidth={isActive ? 2.5 : 1.8}
                                                        style={{
                                                            transition: 'all 0.15s ease',
                                                            filter: isActive
                                                                ? 'drop-shadow(0 3px 6px rgba(200,16,46,0.6))'
                                                                : 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))',
                                                        }}
                                                    />

                                                    {/* Text: flip back right-side-up ONLY if root transform has flipped Y axis */}
                                                    <g transform={`translate(${coords.x}, ${coords.y})${isYFlipped ? ' scale(1, -1)' : ''}`}>
                                                        <text
                                                            x="0"
                                                            y="0"
                                                            textAnchor="middle"
                                                            dominantBaseline="central"
                                                            fontSize={fontSz}
                                                            fontWeight="800"
                                                            fill="#ffffff"
                                                            style={{ pointerEvents: 'none', userSelect: 'none' }}
                                                        >
                                                            {elemRef}
                                                        </text>
                                                    </g>


                                                    {/* Hover Tooltip: flip back ONLY if root transform has flipped Y */}
                                                    {isHovered && (
                                                        <g transform={`translate(${coords.x + 18}, ${coords.y - 12})${isYFlipped ? ' scale(1, -1)' : ''}`}>
                                                            <rect
                                                                x="0"
                                                                y="-20"
                                                                width={Math.max(130, getPartNameForRef(elemRef).length * 7)}
                                                                height="26"
                                                                rx="6"
                                                                fill="#0f172a"
                                                                opacity="0.95"
                                                            />
                                                            <text
                                                                x="8"
                                                                y="-4"
                                                                fontSize="10"
                                                                fontWeight="600"
                                                                fill="#ffffff"
                                                            >
                                                                Ref #{elemRef}: {getPartNameForRef(elemRef).slice(0, 22)}
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
