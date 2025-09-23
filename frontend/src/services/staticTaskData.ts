/**
 * Static Task Data for Fallback
 *
 * Provides static task templates as fallback when API is unavailable.
 * This ensures the application remains functional in offline scenarios.
 */

import { TaskTemplate, TaskListParams } from '../types/tasks';

/**
 * Static task templates - fallback data
 */
const STATIC_TASKS: TaskTemplate[] = [
  {
    id: 'molecular-docking-basic',
    name: 'Basic Molecular Docking',
    description: 'Standard molecular docking analysis using AutoDock Vina',
    category: 'docking',
    subcategory: 'basic',
    tags: ['vina', 'protein', 'ligand'],
    engine: 'vina',
    version: '1.0.0',
    status: 'active',
    parameters: [
      {
        name: 'receptor_file',
        type: 'file',
        required: true,
        description: 'Receptor protein structure file (PDB/PDBQT)',
        validation: {
          file_types: ['.pdb', '.pdbqt'],
          max_size_mb: 100,
        },
      },
      {
        name: 'ligand_file',
        type: 'file',
        required: true,
        description: 'Ligand structure file (SDF/MOL2/PDBQT)',
        validation: {
          file_types: ['.sdf', '.mol2', '.pdbqt'],
          max_size_mb: 10,
        },
      },
      {
        name: 'center_x',
        type: 'number',
        required: true,
        description: 'X coordinate of binding site center',
        default: 0.0,
        validation: {
          min: -1000,
          max: 1000,
        },
      },
      {
        name: 'center_y',
        type: 'number',
        required: true,
        description: 'Y coordinate of binding site center',
        default: 0.0,
        validation: {
          min: -1000,
          max: 1000,
        },
      },
      {
        name: 'center_z',
        type: 'number',
        required: true,
        description: 'Z coordinate of binding site center',
        default: 0.0,
        validation: {
          min: -1000,
          max: 1000,
        },
      },
      {
        name: 'size_x',
        type: 'number',
        required: true,
        description: 'Search space size in X dimension',
        default: 20.0,
        validation: {
          min: 1,
          max: 100,
        },
      },
      {
        name: 'size_y',
        type: 'number',
        required: true,
        description: 'Search space size in Y dimension',
        default: 20.0,
        validation: {
          min: 1,
          max: 100,
        },
      },
      {
        name: 'size_z',
        type: 'number',
        required: true,
        description: 'Search space size in Z dimension',
        default: 20.0,
        validation: {
          min: 1,
          max: 100,
        },
      },
      {
        name: 'num_modes',
        type: 'integer',
        required: false,
        description: 'Number of binding modes to generate',
        default: 9,
        validation: {
          min: 1,
          max: 20,
        },
      },
      {
        name: 'exhaustiveness',
        type: 'integer',
        required: false,
        description: 'Search exhaustiveness level',
        default: 8,
        validation: {
          min: 1,
          max: 32,
        },
      },
    ],
    outputs: [
      {
        name: 'docked_poses',
        type: 'file',
        description: 'Docked ligand poses with scores',
        file_pattern: '*_docked.pdbqt',
      },
      {
        name: 'binding_log',
        type: 'file',
        description: 'Docking log with energies and statistics',
        file_pattern: '*_log.txt',
      },
      {
        name: 'visualization',
        type: 'file',
        description: 'PyMOL visualization script',
        file_pattern: '*_viz.pml',
      },
    ],
    execution_time_estimate: 300,
    resource_requirements: {
      cpu_cores: 4,
      memory_gb: 8,
      disk_gb: 2,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'molecular-docking-advanced',
    name: 'Advanced Molecular Docking',
    description: 'Advanced molecular docking with flexible residues and custom scoring',
    category: 'docking',
    subcategory: 'advanced',
    tags: ['vina', 'flexible', 'custom-scoring'],
    engine: 'vina',
    version: '1.1.0',
    status: 'active',
    parameters: [
      {
        name: 'receptor_file',
        type: 'file',
        required: true,
        description: 'Receptor protein structure file (PDB/PDBQT)',
        validation: {
          file_types: ['.pdb', '.pdbqt'],
          max_size_mb: 100,
        },
      },
      {
        name: 'ligand_file',
        type: 'file',
        required: true,
        description: 'Ligand structure file (SDF/MOL2/PDBQT)',
        validation: {
          file_types: ['.sdf', '.mol2', '.pdbqt'],
          max_size_mb: 10,
        },
      },
      {
        name: 'flexible_residues',
        type: 'string',
        required: false,
        description: 'Comma-separated list of flexible residue IDs',
        validation: {
          pattern: '^[A-Z0-9,\\s]*$',
        },
      },
      {
        name: 'scoring_function',
        type: 'select',
        required: false,
        description: 'Custom scoring function',
        default: 'vina',
        options: ['vina', 'ad4', 'vinardo'],
        validation: {
          allowed_values: ['vina', 'ad4', 'vinardo'],
        },
      },
      {
        name: 'energy_range',
        type: 'number',
        required: false,
        description: 'Energy range for pose selection (kcal/mol)',
        default: 3.0,
        validation: {
          min: 0.1,
          max: 10.0,
        },
      },
    ],
    outputs: [
      {
        name: 'docked_poses',
        type: 'file',
        description: 'Docked ligand poses with detailed scores',
        file_pattern: '*_docked_detailed.pdbqt',
      },
      {
        name: 'binding_analysis',
        type: 'file',
        description: 'Detailed binding analysis report',
        file_pattern: '*_analysis.json',
      },
      {
        name: 'interaction_map',
        type: 'file',
        description: 'Protein-ligand interaction map',
        file_pattern: '*_interactions.png',
      },
    ],
    execution_time_estimate: 900,
    resource_requirements: {
      cpu_cores: 8,
      memory_gb: 16,
      disk_gb: 5,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'protein-preparation',
    name: 'Protein Preparation',
    description: 'Prepare protein structures for molecular docking',
    category: 'preparation',
    subcategory: 'protein',
    tags: ['preparation', 'protein', 'cleanup'],
    engine: 'internal',
    version: '1.0.0',
    status: 'active',
    parameters: [
      {
        name: 'protein_file',
        type: 'file',
        required: true,
        description: 'Raw protein structure file (PDB)',
        validation: {
          file_types: ['.pdb'],
          max_size_mb: 50,
        },
      },
      {
        name: 'remove_water',
        type: 'boolean',
        required: false,
        description: 'Remove water molecules',
        default: true,
      },
      {
        name: 'add_hydrogens',
        type: 'boolean',
        required: false,
        description: 'Add hydrogen atoms',
        default: true,
      },
      {
        name: 'optimize_sidechains',
        type: 'boolean',
        required: false,
        description: 'Optimize side chain conformations',
        default: false,
      },
    ],
    outputs: [
      {
        name: 'prepared_protein',
        type: 'file',
        description: 'Prepared protein structure',
        file_pattern: '*_prepared.pdb',
      },
      {
        name: 'preparation_log',
        type: 'file',
        description: 'Preparation process log',
        file_pattern: '*_prep_log.txt',
      },
    ],
    execution_time_estimate: 120,
    resource_requirements: {
      cpu_cores: 2,
      memory_gb: 4,
      disk_gb: 1,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

/**
 * Get static task templates with optional filtering
 */
export function getStaticTaskTemplates(params?: TaskListParams): TaskTemplate[] {
  let filteredTasks = [...STATIC_TASKS];

  if (params?.category) {
    filteredTasks = filteredTasks.filter((task) => task.category === params.category);
  }

  if (params?.engine) {
    filteredTasks = filteredTasks.filter((task) => task.engine === params.engine);
  }

  if (params?.status) {
    filteredTasks = filteredTasks.filter((task) => task.status === params.status);
  }

  if (params?.search) {
    const searchLower = params.search.toLowerCase();
    filteredTasks = filteredTasks.filter(
      (task) =>
        task.name.toLowerCase().includes(searchLower) ||
        task.description.toLowerCase().includes(searchLower) ||
        task.tags.some((tag) => tag.toLowerCase().includes(searchLower)),
    );
  }

  // Apply pagination
  if (params?.offset || params?.limit) {
    const offset = params.offset || 0;
    const limit = params.limit || 50;
    filteredTasks = filteredTasks.slice(offset, offset + limit);
  }

  return filteredTasks;
}

/**
 * Get unique categories from static tasks
 */
export function getStaticTaskCategories(): string[] {
  const categories = new Set(STATIC_TASKS.map((task) => task.category));
  return Array.from(categories).sort();
}

/**
 * Get static task by ID
 */
export function getStaticTaskById(id: string): TaskTemplate | undefined {
  return STATIC_TASKS.find((task) => task.id === id);
}

/**
 * Get static tasks count
 */
export function getStaticTasksCount(): number {
  return STATIC_TASKS.length;
}
