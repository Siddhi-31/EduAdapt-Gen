import React, { useState, useEffect } from 'react';
import { fetchCurriculumTopics, searchCurriculum } from '../api/learningApi';
import { Icon, Spinner, StatusPill } from '../components/ui';

const PPS_UNITS_DATA = [
  {
    unit_id: 'unit_1',
    title: 'Unit 1: Fundamentals of Computing & C',
    co: 'CO1',
    description: 'Data types, memory size, variable declaration, operator precedence, type casting.',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    unit_id: 'unit_2',
    title: 'Unit 2: Control Flow & Logic',
    co: 'CO2',
    description: 'Decision branches if-else, switch-case, for/while/do-while loops, break and continue.',
    topics: ['Conditionals', 'Loops'],
  },
  {
    unit_id: 'unit_3',
    title: 'Unit 3: Arrays & Strings',
    co: 'CO3',
    description: 'Contiguous memory allocation, 1D/2D arrays, null-terminated strings, string library.',
    topics: ['Arrays', 'Strings'],
  },
  {
    unit_id: 'unit_4',
    title: 'Unit 4: Functions & Pointers',
    co: 'CO4',
    description: 'Modular design, stack frames, pointer dereferencing, pointer arithmetic, call by reference.',
    topics: ['Functions', 'Pointers'],
  },
  {
    unit_id: 'unit_5',
    title: 'Unit 5: Structures & Dynamic Memory Allocation',
    co: 'CO5',
    description: 'User-defined types, memory alignment, malloc, calloc, realloc, and free on heap.',
    topics: ['Structures', 'Dynamic Memory Allocation'],
  },
];

export default function CurriculumPage({
  currentTopic,
  onSelectTopic,
  onNavigate,
}) {
  const [units, setUnits] = useState(PPS_UNITS_DATA);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);

  useEffect(() => {
    fetchCurriculumTopics()
      .then((data) => {
        if (data && data.units && data.units.length > 0) {
          // Merge API topics with our metadata
          const merged = PPS_UNITS_DATA.map((u, i) => ({
            ...u,
            ...(data.units[i] || {}),
          }));
          setUnits(merged);
        }
      })
      .catch((err) => console.warn('Curriculum topics load notice:', err));
  }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await searchCurriculum(searchQuery, 4);
      setSearchResults(data.results || data.chunks || []);
    } catch (err) {
      setSearchError('Course search is temporarily unavailable. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleChooseTopic = (topic) => {
    if (onSelectTopic) onSelectTopic(topic);
    if (onNavigate) onNavigate('learn');
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <span className="eyebrow plain">Syllabus & Course Content</span>
          <h1>PPS Course Curriculum</h1>
          <p className="muted">
            Explore all 5 core syllabus units and search lecture slides for key concepts, definitions, and code examples.
          </p>
        </div>
      </div>

      {/* Curriculum Search Box */}
      <div className="card">
        <div className="row between">
          <div>
            <h3>Curriculum Search</h3>
            <p className="hint">Find topics, lecture explanations, and programming patterns from your course slides.</p>
          </div>
          <span className="pill violet">Course Syllabus</span>
        </div>

        <form onSubmit={handleSearch} className="row mt16">
          <input
            type="text"
            className="input grow"
            placeholder="e.g. pointer dereferencing, heap memory allocation, array indexing..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={isSearching}
          />
          <button type="submit" className="btn primary" disabled={isSearching || !searchQuery.trim()}>
            {isSearching ? <Spinner /> : <><Icon name="search" size={16} /> Search</>}
          </button>
        </form>

        {searchError && <p className="error mt8">{searchError}</p>}

        {searchResults.length > 0 && (
          <div className="col mt16" style={{ gap: 10 }}>
            <span className="small muted">Relevant Course Topics ({searchResults.length}):</span>
            {searchResults.map((res, idx) => (
              <div key={idx} className="card soft col" style={{ padding: 14, gap: 6 }}>
                <div className="row between">
                  <strong className="small">{res.topic || res.unit || `Topic #${idx + 1}`}</strong>
                  {res.similarity !== undefined && (
                    <span className="pill green">Relevance: {Math.round(res.similarity * 100)}%</span>
                  )}
                </div>
                <p className="small" style={{ lineHeight: 1.6 }}>{res.text || res.content}</p>
                {res.topic && (
                  <div className="row mt8">
                    <button
                      type="button"
                      className="btn sm"
                      onClick={() => handleChooseTopic(res.topic)}
                    >
                      Open Lesson for {res.topic} →
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Curriculum Units Grid */}
      <div className="grid g2">
        {units.map((unit) => (
          <div key={unit.unit_id || unit.title} className="card col" style={{ gap: 14 }}>
            <div className="row between">
              <span className="eyebrow">{unit.co || 'PPS'}</span>
              <span className="pill">{unit.topics?.length || 2} Topics</span>
            </div>

            <div>
              <h3>{unit.title}</h3>
              <p className="hint mt8">{unit.description}</p>
            </div>

            <div className="col mt8" style={{ gap: 8 }}>
              {unit.topics.map((top) => {
                const isCurrent = top === currentTopic;
                return (
                  <div key={top} className="list-item" style={{ padding: '8px 0' }}>
                    <span className={`dot ${isCurrent ? 'now' : 'done'}`} />
                    <span className="grow small" style={{ fontWeight: isCurrent ? 600 : 400 }}>
                      {top} {isCurrent && <span className="pill violet" style={{ marginLeft: 6 }}>Active</span>}
                    </span>
                    <button
                      type="button"
                      className={`btn sm ${isCurrent ? 'primary' : ''}`}
                      onClick={() => handleChooseTopic(top)}
                    >
                      {isCurrent ? 'Resume' : 'Learn'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
