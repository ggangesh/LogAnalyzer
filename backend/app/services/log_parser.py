import re
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LogFormat(Enum):
    """Supported log formats"""
    UNKNOWN = "unknown"
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    YAML = "yaml"
    STRUCTURED = "structured"  # Common log formats like syslog, apache, nginx
    PLAIN = "plain"  # Plain text logs

@dataclass
class LogEntry:
    """Represents a parsed log entry"""
    timestamp: Optional[datetime]
    level: Optional[str]
    message: str
    source: str
    raw_line: str
    parsed_data: Dict[str, Any]
    line_number: int

@dataclass
class ParseResult:
    """Result of log parsing operation"""
    entries: List[LogEntry]
    format_detected: LogFormat
    total_lines: int
    parsed_lines: int
    errors: List[str]
    dataframe: Optional[pd.DataFrame]

class LogParser:
    """Comprehensive log parsing engine with format detection and pandas integration"""
    
    def __init__(self):
        # Common timestamp patterns
        self.timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)',  # ISO format
            r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)',  # MM/DD/YYYY HH:MM:SS
            r'(\d{2}-\d{2}-\d{4}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)',  # MM-DD-YYYY HH:MM:SS
            r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)',  # YYYY/MM/DD HH:MM:SS
            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',  # Mon DD HH:MM:SS
        ]
        
        # Log level patterns
        self.level_patterns = [
            r'\b(ERROR|WARN|WARNING|INFO|DEBUG|CRITICAL|FATAL)\b',
            r'\[(ERROR|WARN|WARNING|INFO|DEBUG|CRITICAL|FATAL)\]',
            r'"(level|severity)":\s*"(ERROR|WARN|WARNING|INFO|DEBUG|CRITICAL|FATAL)"',
        ]
        
        # Common structured log patterns
        self.structured_patterns = {
            'apache': r'(\S+) - - \[([^\]]+)\] "([^"]*)" (\d+) (\d+)',
            'nginx': r'(\S+) - (\S+) \[([^\]]+)\] "([^"]*)" (\d+) (\d+)',
            'syslog': r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.+)',
            'json': r'\{.*\}',
        }
        
        # Compile regex patterns for performance
        self.compiled_timestamp_patterns = [re.compile(pattern) for pattern in self.timestamp_patterns]
        self.compiled_level_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.level_patterns]
        self.compiled_structured_patterns = {
            name: re.compile(pattern) for name, pattern in self.structured_patterns.items()
        }

    def detect_format(self, file_path: Union[str, Path]) -> LogFormat:
        """Detect the format of the log file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to detect format
                sample_lines = []
                for i, line in enumerate(f):
                    if i >= 10:  # Check first 10 lines
                        break
                    sample_lines.append(line.strip())
                
                if not sample_lines:
                    return LogFormat.UNKNOWN
                
                # Check for JSON format
                json_count = 0
                for line in sample_lines:
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        try:
                            json.loads(line)
                            json_count += 1
                        except json.JSONDecodeError:
                            pass
                
                if json_count >= len(sample_lines) * 0.7:  # 70% JSON lines
                    return LogFormat.JSON
                
                # Check for CSV format
                csv_count = 0
                for line in sample_lines:
                    if ',' in line and line.count(',') >= 2:
                        csv_count += 1
                
                if csv_count >= len(sample_lines) * 0.7:
                    return LogFormat.CSV
                
                # Check for XML format
                xml_count = 0
                for line in sample_lines:
                    if '<' in line and '>' in line:
                        xml_count += 1
                
                if xml_count >= len(sample_lines) * 0.7:
                    return LogFormat.XML
                
                # Check for YAML format
                yaml_count = 0
                for line in sample_lines:
                    if ':' in line and not line.strip().startswith('#'):
                        yaml_count += 1
                
                if yaml_count >= len(sample_lines) * 0.7:
                    return LogFormat.YAML
                
                # Check for structured logs
                structured_count = 0
                for line in sample_lines:
                    for pattern in self.compiled_structured_patterns.values():
                        if pattern.search(line):
                            structured_count += 1
                            break
                
                if structured_count >= len(sample_lines) * 0.5:
                    return LogFormat.STRUCTURED
                
                return LogFormat.PLAIN
                
        except Exception as e:
            logger.error(f"Error detecting format: {e}")
            return LogFormat.UNKNOWN

    def parse_timestamp(self, text: str) -> Optional[datetime]:
        """Parse timestamp from text using multiple patterns"""
        for pattern in self.compiled_timestamp_patterns:
            match = pattern.search(text)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Try different timestamp formats
                    for fmt in [
                        '%Y-%m-%dT%H:%M:%S.%fZ',
                        '%Y-%m-%dT%H:%M:%SZ',
                        '%Y-%m-%dT%H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%d %H:%M:%S',
                        '%m/%d/%Y %H:%M:%S.%f',
                        '%m/%d/%Y %H:%M:%S',
                        '%m-%d-%Y %H:%M:%S.%f',
                        '%m-%d-%Y %H:%M:%S',
                        '%Y/%m/%d %H:%M:%S.%f',
                        '%Y/%m/%d %H:%M:%S',
                        '%b %d %H:%M:%S',
                    ]:
                        try:
                            return datetime.strptime(timestamp_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None

    def parse_level(self, text: str) -> Optional[str]:
        """Parse log level from text"""
        for pattern in self.compiled_level_patterns:
            match = pattern.search(text)
            if match:
                level = match.group(1)
                return level.upper()
        return None

    def parse_json_log(self, line: str, line_number: int, source: str) -> Optional[LogEntry]:
        """Parse JSON formatted log entry"""
        try:
            data = json.loads(line)
            
            # Extract common fields
            timestamp = None
            if 'timestamp' in data:
                timestamp = self.parse_timestamp(str(data['timestamp']))
            elif 'time' in data:
                timestamp = self.parse_timestamp(str(data['time']))
            elif 'date' in data:
                timestamp = self.parse_timestamp(str(data['date']))
            
            level = data.get('level', data.get('severity', data.get('log_level')))
            message = data.get('message', data.get('msg', data.get('text', str(data))))
            
            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source=source,
                raw_line=line,
                parsed_data=data,
                line_number=line_number
            )
        except json.JSONDecodeError:
            return None

    def parse_structured_log(self, line: str, line_number: int, source: str) -> Optional[LogEntry]:
        """Parse structured log entry (Apache, Nginx, Syslog, etc.)"""
        for log_type, pattern in self.compiled_structured_patterns.items():
            match = pattern.search(line)
            if match:
                if log_type == 'apache':
                    ip, timestamp_str, request, status, size = match.groups()
                    timestamp = self.parse_timestamp(timestamp_str)
                    return LogEntry(
                        timestamp=timestamp,
                        level=None,
                        message=f"HTTP {status}: {request}",
                        source=source,
                        raw_line=line,
                        parsed_data={
                            'ip': ip,
                            'timestamp': timestamp_str,
                            'request': request,
                            'status': status,
                            'size': size,
                            'log_type': 'apache'
                        },
                        line_number=line_number
                    )
                elif log_type == 'nginx':
                    ip, user, timestamp_str, request, status, size = match.groups()
                    timestamp = self.parse_timestamp(timestamp_str)
                    return LogEntry(
                        timestamp=timestamp,
                        level=None,
                        message=f"HTTP {status}: {request}",
                        source=source,
                        raw_line=line,
                        parsed_data={
                            'ip': ip,
                            'user': user,
                            'timestamp': timestamp_str,
                            'request': request,
                            'status': status,
                            'size': size,
                            'log_type': 'nginx'
                        },
                        line_number=line_number
                    )
                elif log_type == 'syslog':
                    timestamp_str, host, program, message = match.groups()
                    timestamp = self.parse_timestamp(timestamp_str)
                    level = self.parse_level(message)
                    return LogEntry(
                        timestamp=timestamp,
                        level=level,
                        message=message,
                        source=source,
                        raw_line=line,
                        parsed_data={
                            'timestamp': timestamp_str,
                            'host': host,
                            'program': program,
                            'log_type': 'syslog'
                        },
                        line_number=line_number
                    )
        return None

    def parse_plain_log(self, line: str, line_number: int, source: str) -> LogEntry:
        """Parse plain text log entry"""
        timestamp = self.parse_timestamp(line)
        level = self.parse_level(line)
        
        # Extract message (everything after timestamp and level)
        message = line
        if timestamp:
            # Remove timestamp from message
            for pattern in self.compiled_timestamp_patterns:
                message = pattern.sub('', message).strip()
        
        if level:
            # Remove level from message
            for pattern in self.compiled_level_patterns:
                message = pattern.sub('', message).strip()
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message,
            source=source,
            raw_line=line,
            parsed_data={'log_type': 'plain'},
            line_number=line_number
        )

    def parse_file(self, file_path: Union[str, Path]) -> ParseResult:
        """Parse log file and return structured data"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        format_detected = self.detect_format(file_path)
        entries = []
        errors = []
        total_lines = 0
        parsed_lines = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_number, line in enumerate(f, 1):
                    total_lines += 1
                    line = line.strip()
                    
                    if not line:  # Skip empty lines
                        continue
                    
                    try:
                        entry = None
                        
                        if format_detected == LogFormat.JSON:
                            entry = self.parse_json_log(line, line_number, str(file_path))
                        elif format_detected == LogFormat.STRUCTURED:
                            entry = self.parse_structured_log(line, line_number, str(file_path))
                        else:  # PLAIN or other formats
                            entry = self.parse_plain_log(line, line_number, str(file_path))
                        
                        if entry:
                            entries.append(entry)
                            parsed_lines += 1
                        else:
                            errors.append(f"Line {line_number}: Could not parse line")
                            
                    except Exception as e:
                        errors.append(f"Line {line_number}: {str(e)}")
                        continue
            
            # Create pandas DataFrame
            dataframe = None
            if entries:
                df_data = []
                for entry in entries:
                    row = {
                        'timestamp': entry.timestamp,
                        'level': entry.level,
                        'message': entry.message,
                        'source': entry.source,
                        'line_number': entry.line_number,
                        'raw_line': entry.raw_line
                    }
                    # Add parsed data fields
                    for key, value in entry.parsed_data.items():
                        row[f'parsed_{key}'] = value
                    df_data.append(row)
                
                dataframe = pd.DataFrame(df_data)
                # Convert timestamp column to datetime
                if 'timestamp' in dataframe.columns:
                    dataframe['timestamp'] = pd.to_datetime(dataframe['timestamp'])
            
            return ParseResult(
                entries=entries,
                format_detected=format_detected,
                total_lines=total_lines,
                parsed_lines=parsed_lines,
                errors=errors,
                dataframe=dataframe
            )
            
        except Exception as e:
            raise Exception(f"Error parsing file {file_path}: {str(e)}")

    def filter_by_time_range(self, entries: List[LogEntry], 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> List[LogEntry]:
        """Filter log entries by time range"""
        filtered_entries = []
        
        for entry in entries:
            if entry.timestamp is None:
                continue
                
            # Check if entry is within time range
            if start_time and entry.timestamp < start_time:
                continue
            if end_time and entry.timestamp > end_time:
                continue
                
            filtered_entries.append(entry)
        
        return filtered_entries

    def get_quick_filters(self) -> Dict[str, Dict[str, datetime]]:
        """Get predefined time filter ranges"""
        now = datetime.now()
        return {
            'last_1h': {
                'start': now - timedelta(hours=1),
                'end': now
            },
            'last_24h': {
                'start': now - timedelta(hours=24),
                'end': now
            },
            'last_7d': {
                'start': now - timedelta(days=7),
                'end': now
            },
            'last_30d': {
                'start': now - timedelta(days=30),
                'end': now
            },
            'today': {
                'start': now.replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now
            },
            'yesterday': {
                'start': (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
                'end': now.replace(hour=0, minute=0, second=0, microsecond=0)
            }
        } 