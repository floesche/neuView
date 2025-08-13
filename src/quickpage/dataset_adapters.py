"""
Dataset adapters for handling differences between NeuPrint datasets.

Different NeuPrint datasets (hemibrain, cns, optic-lobe) have varying
database structures and property names. These adapters normalize
the differences and provide a consistent interface.
"""

import re
import pandas as pd
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Type, Dict, Any
from dataclasses import dataclass, field


@dataclass
class DatasetInfo:
    """Information about a dataset structure."""
    name: str
    soma_side_column: Optional[str] = None
    soma_side_extraction: Optional[str] = None  # regex pattern
    pre_synapse_column: str = "pre"
    post_synapse_column: str = "post"
    instance_column: str = "instance"
    type_column: str = "type"
    body_id_column: str = "bodyId"
    roi_columns: Optional[List[str]] = None

    def __post_init__(self):
        if self.roi_columns is None:
            self.roi_columns = ["inputRois", "outputRois"]


class DatasetAdapter(ABC):
    """Base class for dataset-specific adapters."""
    
    def __init__(self, dataset_info: Optional[DatasetInfo] = None):
        self.dataset_info = dataset_info
    
    @abstractmethod
    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Extract soma side information from the dataset."""
        pass
    
    @abstractmethod
    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format."""
        pass
    
    @abstractmethod
    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get total pre and post synapse counts."""
        pass
    
    def filter_by_soma_side(self, neurons_df: pd.DataFrame, soma_side: str) -> pd.DataFrame:
        """Filter neurons by soma side."""
        if soma_side == 'both' or soma_side == 'all':
            return neurons_df
        
        # Ensure soma side is extracted
        neurons_df = self.extract_soma_side(neurons_df)
        
        if 'somaSide' not in neurons_df.columns:
            dataset_name = self.dataset_info.name if self.dataset_info else "unknown"
            raise ValueError(f"Cannot filter by soma side for dataset {dataset_name}")
        
        # Handle both 'L'/'R' and 'left'/'right' formats
        side_filter = None
        if soma_side.lower() in ['left', 'l']:
            side_filter = 'L'
        elif soma_side.lower() in ['right', 'r']:
            side_filter = 'R'
        elif soma_side.lower() in ['middle', 'm']:
            side_filter = 'M'
        else:
            raise ValueError(f"Invalid soma side: {soma_side}. Use 'L', 'R', 'M', 'left', 'right', 'middle', 'both', or 'all'")
        
        return neurons_df[neurons_df['somaSide'] == side_filter]
    
    def get_available_columns(self, neurons_df: pd.DataFrame) -> List[str]:
        """Get list of available columns in the dataset."""
        return list(neurons_df.columns)


class CNSAdapter(DatasetAdapter):
    """Adapter for CNS dataset."""
    
    def __init__(self):
        dataset_info = DatasetInfo(
            name="cns",
            soma_side_column="somaSide",
            pre_synapse_column="pre",
            post_synapse_column="post",
            roi_columns=["inputRois", "outputRois"]
        )
        super().__init__(dataset_info)

    def has_soma_side_column(self) -> Optional[str]:
        """ Return the name of the column in the database with soma side information. 
        If None, then the column does not exist in the database."""
        return self.dataset_info.soma_side_column

    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """CNS has a dedicated somaSide column."""
        if 'somaSide' in neurons_df.columns:
            return neurons_df
        else:
            # If somaSide column doesn't exist, create it as unknown
            neurons_df = neurons_df.copy()
            neurons_df['somaSide'] = 'U'  # Unknown
            return neurons_df
    
    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """CNS columns are already in standard format."""
        return neurons_df
    
    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get synapse counts from CNS dataset."""
        pre_total = neurons_df[self.dataset_info.pre_synapse_column].sum() if self.dataset_info.pre_synapse_column in neurons_df.columns else 0
        post_total = neurons_df[self.dataset_info.post_synapse_column].sum() if self.dataset_info.post_synapse_column in neurons_df.columns else 0
        return int(pre_total), int(post_total)


class HemibrainAdapter(DatasetAdapter):
    """Adapter for Hemibrain dataset."""
    
    def __init__(self):
        dataset_info = DatasetInfo(
            name="hemibrain",
            pre_synapse_column="pre",
            post_synapse_column="post",
            roi_columns=["inputRois", "outputRois"]
        )
        super().__init__(dataset_info)

    def has_soma_side_column(self) -> Optional[str]:
        """ Return the name of the column in the database with soma side information. 
        If None, then the column does not exist in the database."""
        return self.dataset_info.soma_side_column

    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Hemibrain dataset does not have a somaSide column."""
        if 'somaSide' in neurons_df.columns:
            return neurons_df
        else:
            # If missing, try to extract from instance name
            neurons_df = neurons_df.copy()
            if 'instance' in neurons_df.columns:
                # Extract from instance names like "neuronType_R" or "neuronType_L"
                neurons_df['somaSide'] = neurons_df['instance'].str.extract(r'_([LR])$')[0]
                neurons_df['somaSide'] = neurons_df['somaSide'].fillna('U')
            else:
                neurons_df['somaSide'] = 'U'
            return neurons_df
    
    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize Hemibrain columns."""
        return neurons_df
    
    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get synapse counts from Hemibrain dataset."""
        pre_total = neurons_df[self.dataset_info.pre_synapse_column].sum() if self.dataset_info.pre_synapse_column in neurons_df.columns else 0
        post_total = neurons_df[self.dataset_info.post_synapse_column].sum() if self.dataset_info.post_synapse_column in neurons_df.columns else 0
        return int(pre_total), int(post_total)


class OpticLobeAdapter(DatasetAdapter):
    """Adapter for Optic Lobe dataset."""
    
    def __init__(self):
        dataset_info = DatasetInfo(
            name="optic-lobe",
            soma_side_extraction=r'_([LRM])(?:_|$)',  # Extract L, R, or M from instance names
            pre_synapse_column="pre",
            post_synapse_column="post",
            roi_columns=["inputRois", "outputRois"]
        )
        super().__init__(dataset_info)
    
    def has_soma_side_column(self) -> Optional[str]:
        """ Return the name of the column in the database with soma side information. 
        If None, then the column does not exist in the database."""
        return self.dataset_info.soma_side_column
    
    def extract_soma_side(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Extract soma side from instance names using regex."""
        neurons_df = neurons_df.copy()
        
        if 'somaSide' in neurons_df.columns:
            return neurons_df
        
        if 'instance' in neurons_df.columns and self.dataset_info.soma_side_extraction:
            # Extract soma side from instance names
            # Patterns like: "LC4_L", "LPLC2_R_001", "T4_L_medulla"
            pattern = self.dataset_info.soma_side_extraction
            extracted = neurons_df['instance'].str.extract(pattern, expand=False)
            neurons_df['somaSide'] = extracted.fillna('U')  # Unknown if not found
        else:
            neurons_df['somaSide'] = 'U'

        return neurons_df
    
    def normalize_columns(self, neurons_df: pd.DataFrame) -> pd.DataFrame:
        """Normalize Optic Lobe columns."""
        # Optic lobe might have different column names
        column_mapping = {
            # Add any column name mappings specific to optic lobe
            # 'old_name': 'new_name'
        }
        
        if column_mapping:
            neurons_df = neurons_df.rename(columns=column_mapping)
        
        return neurons_df
    
    def get_synapse_counts(self, neurons_df: pd.DataFrame) -> Tuple[int, int]:
        """Get synapse counts from Optic Lobe dataset."""
        pre_total = neurons_df[self.dataset_info.pre_synapse_column].sum() if self.dataset_info.pre_synapse_column in neurons_df.columns else 0
        post_total = neurons_df[self.dataset_info.post_synapse_column].sum() if self.dataset_info.post_synapse_column in neurons_df.columns else 0
        return int(pre_total), int(post_total)


class DatasetAdapterFactory:
    """Factory for creating dataset adapters."""
    
    _adapters: Dict[str, Type[DatasetAdapter]] = {
        'cns': CNSAdapter,
        'hemibrain': HemibrainAdapter,
        'optic-lobe': OpticLobeAdapter
    }
    
    @classmethod
    def create_adapter(cls, dataset_name: str) -> DatasetAdapter:
        """Create appropriate adapter for the dataset."""
        # Handle versioned dataset names
        base_name = dataset_name.split(':')[0] if ':' in dataset_name else dataset_name
        
        if dataset_name in cls._adapters:
            return cls._adapters[dataset_name]()
        elif base_name in cls._adapters:
            return cls._adapters[base_name]()
        else:
            # Default to CNS adapter for unknown datasets
            print(f"Warning: Unknown dataset '{dataset_name}', using CNS adapter as default")
            return CNSAdapter()
    
    @classmethod
    def register_adapter(cls, dataset_name: str, adapter_class: type):
        """Register a new adapter for a dataset."""
        cls._adapters[dataset_name] = adapter_class
    
    @classmethod
    def get_supported_datasets(cls) -> List[str]:
        """Get list of supported datasets."""
        return list(cls._adapters.keys())


def get_dataset_adapter(dataset_name: str) -> DatasetAdapter:
    """Convenience function to get dataset adapter."""
    return DatasetAdapterFactory.create_adapter(dataset_name)
