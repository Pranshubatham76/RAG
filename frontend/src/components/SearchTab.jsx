import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Link,
  Divider,
} from '@mui/material';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import axios from 'axios';

function SearchTab() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post('/api/v1/search', {
        query: query.trim(),
        top_k: topK,
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Search Chunks
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Search the vector database for similar chunks (no LLM processing)
      </Typography>
      
      <form onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Search query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          margin="normal"
          required
          multiline
          rows={3}
          disabled={loading}
          placeholder="e.g., reading club discussion"
        />
        
        <TextField
          label="Number of results"
          type="number"
          value={topK}
          onChange={(e) => setTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
          margin="normal"
          sx={{ width: 200 }}
          inputProps={{ min: 1, max: 20 }}
          disabled={loading}
        />
        
        <Button
          type="submit"
          variant="contained"
          disabled={loading || !query.trim()}
          sx={{ mt: 2, ml: 2 }}
        >
          {loading ? <CircularProgress size={24} /> : 'Search'}
        </Button>
      </form>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          <Typography variant="body2" fontWeight="bold">Error:</Typography>
          <Typography variant="body2">{error}</Typography>
        </Alert>
      )}

      {result && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Search Results
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Chip 
                label={`Query: ${result.query}`} 
                color="primary" 
                size="small" 
                sx={{ mr: 1 }}
              />
              <Chip 
                label={`Results: ${result.count || 0}`} 
                color="secondary" 
                size="small" 
              />
            </Box>

            {result.results && result.results.length > 0 && (
              <List>
                {result.results.map((item, index) => (
                  <ListItem 
                    key={index} 
                    divider
                    sx={{ 
                      flexDirection: 'column', 
                      alignItems: 'stretch',
                      py: 2
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle2" fontWeight="bold">
                        Result {index + 1}
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {item.similarity !== undefined && (
                          <Chip 
                            label={`${(item.similarity * 100).toFixed(1)}% match`} 
                            size="small" 
                            color="info" 
                            variant="outlined"
                          />
                        )}
                        {item.chunk_id && (
                          <Chip 
                            label={`ID: ${item.chunk_id}`} 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </Box>
                    
                    {item.meta?.title && (
                      <Typography variant="h6" sx={{ mb: 1, fontSize: '1rem' }}>
                        {item.meta.title}
                      </Typography>
                    )}
                    
                    <Typography 
                      variant="body2" 
                      color="text.secondary" 
                      sx={{ 
                        mb: 1.5,
                        p: 1.5,
                        bgcolor: 'grey.50',
                        borderRadius: 1,
                        borderLeft: '3px solid',
                        borderColor: 'secondary.main',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word'
                      }}
                    >
                      {item.text}
                    </Typography>
                    
                    {item.meta && (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                        {item.meta.url && (
                          <Link
                            href={item.meta.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              gap: 0.5,
                              textDecoration: 'none'
                            }}
                          >
                            <OpenInNewIcon fontSize="small" />
                            <Typography variant="caption" color="primary">
                              View Original Post
                            </Typography>
                          </Link>
                        )}
                        {item.meta.post_id && (
                          <Chip 
                            label={`Post #${item.meta.post_id}`} 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                        {item.meta.topic_id && (
                          <Chip 
                            label={`Topic #${item.meta.topic_id}`} 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                        {item.meta.author && (
                          <Chip 
                            label={`By: ${item.meta.author}`} 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                        {item.meta.timestamp && (
                          <Chip 
                            label={new Date(item.meta.timestamp).toLocaleDateString()} 
                            size="small" 
                            variant="outlined"
                          />
                        )}
                      </Box>
                    )}
                  </ListItem>
                ))}
              </List>
            )}
            
            {result.results && result.results.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No results found for this query. Try rephrasing your search or check if data has been indexed.
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
}

export default SearchTab;

